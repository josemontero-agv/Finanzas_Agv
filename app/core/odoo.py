# -*- coding: utf-8 -*-
"""
Repositorio de conexión a Odoo.

Maneja la conexión XML-RPC y autenticación con Odoo.
Patrón Repository para abstraer el acceso a datos de Odoo.

Notas de autenticación:
- Soporta contraseñas normales y API Keys de Odoo (Configuración > Usuarios > API Keys).
- Las API Keys permiten autenticarse sin 2FA/Google Authenticator, ya que
  la autenticación XML-RPC no pasa por el flujo MFA del navegador.
- Para habilitar: generar API Key en Odoo y poner su valor en ODOO_PASSWORD del .env.

Rendimiento:
- call_parallel(): ejecuta múltiples llamadas independientes en paralelo con
  ThreadPoolExecutor, reduciendo el tiempo total de reportes con muchas consultas.
"""

import logging
import threading
import xmlrpc.client
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)


class OdooRepository:
    """
    Repositorio para conexión a Odoo usando XML-RPC.

    Abstrae el acceso a datos y provee métodos convenientes para búsqueda
    y lectura de registros. El UID autenticado se cachea a nivel de clase
    para evitar re-autenticaciones en cada request.

    Soporta API Keys de Odoo como reemplazo de contraseña (para usuarios con 2FA).

    Métodos principales:
        search_read, read, search, search_count, read_group,
        execute_kw, call_parallel, authenticate_user, is_connected
    """

    _cached_uids: Dict = {}
    _lock = threading.Lock()

    def __init__(self, url: str, db: str, username: str, password: str):
        """
        Inicializa la conexión a Odoo.

        Args:
            url (str): URL del servidor Odoo (ej: 'https://odoo.example.com')
            db (str): Nombre de la base de datos
            username (str): Usuario de Odoo
            password (str): Contraseña o API Key del usuario
        """
        self.url = url.rstrip('/')
        self.db = db
        self.username = username
        self.password = password
        self.uid: Optional[int] = None
        self.models = None

        if not all([self.url, self.db, self.username, self.password]):
            raise ValueError("Faltan credenciales de Odoo. Se requieren: url, db, username, password")

        cache_key = f"{self.url}|{self.db}|{self.username}"
        with OdooRepository._lock:
            self.uid = OdooRepository._cached_uids.get(cache_key)

        self._connect()

        if self.uid:
            with OdooRepository._lock:
                OdooRepository._cached_uids[cache_key] = self.uid

    # ------------------------------------------------------------------
    # Conexión
    # ------------------------------------------------------------------

    def _connect(self):
        """Establece la conexión XML-RPC con Odoo."""
        cache_key = f"{self.url}|{self.db}|{self.username}"
        try:
            self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')

            if self.uid:
                # Verificar que el UID cacheado siga siendo válido
                try:
                    self.models.execute_kw(
                        self.db, self.uid, self.password,
                        'res.users', 'read', [[self.uid]], {'fields': ['id']}
                    )
                    return
                except Exception:
                    logger.info("UID de cache expirado o invalido. Re-autenticando...")
                    self.uid = None
                    with OdooRepository._lock:
                        OdooRepository._cached_uids.pop(cache_key, None)

            # Autenticar (soporta contraseña normal y API Keys)
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            self.uid = common.authenticate(self.db, self.username, self.password, {})

            if self.uid:
                logger.info("Conexion a Odoo establecida. UID=%s", self.uid)
            else:
                logger.warning("No se pudo autenticar contra Odoo. Credenciales o API Key invalidas.")
                self.uid = None
                self.models = None

        except Exception as exc:
            logger.error("Error al conectar con Odoo (%s). Continuando sin conexion.", type(exc).__name__)
            self.uid = None
            self.models = None

    # ------------------------------------------------------------------
    # Autenticación de usuarios de la app
    # ------------------------------------------------------------------

    def authenticate_user(self, username: str, password: str) -> bool:
        """
        Autentica un usuario contra Odoo.

        Soporta contraseñas normales y API Keys de Odoo.
        Las API Keys permiten autenticarse incluso con 2FA habilitado:
          1. En Odoo: Configuración → Usuarios → tu usuario → API Keys → Crear
          2. Usa la API Key como contraseña en el formulario de login de la app

        Falla de forma segura (fail-safe): si Odoo no está disponible, la
        autenticación falla. No se usa ningún fallback con credenciales internas.

        Args:
            username (str): Email del usuario en Odoo
            password (str): Contraseña o API Key

        Returns:
            bool: True si la autenticación fue exitosa
        """
        try:
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            uid = common.authenticate(self.db, username, password, {})

            if uid:
                logger.info("Autenticacion exitosa para usuario: %s", username)
                return True

            logger.warning("Credenciales incorrectas para usuario: %s", username)
            return False

        except Exception as exc:
            logger.error(
                "No se pudo conectar a Odoo para autenticar (%s). Servicio no disponible.",
                type(exc).__name__
            )
            return False

    def is_connected(self) -> bool:
        """Verifica si hay conexión activa a Odoo."""
        return bool(self.uid and self.models)

    # ------------------------------------------------------------------
    # Acceso a datos
    # ------------------------------------------------------------------

    def execute_kw(self, model: str, method: str, args: list, kwargs: Optional[dict] = None):
        """
        Wrapper genérico para llamadas execute_kw a Odoo.

        Args:
            model (str): Modelo de Odoo (ej: 'account.move')
            method (str): Método a ejecutar (ej: 'search_read')
            args (list): Argumentos posicionales
            kwargs (dict, optional): Argumentos con nombre

        Returns:
            Resultado de Odoo o None si la conexión falló
        """
        if not self.uid or not self.models:
            logger.warning("No hay conexion a Odoo disponible")
            return None

        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, method, args, kwargs or {}
            )
        except Exception as exc:
            logger.error("Error ejecutando %s.%s: %s", model, method, type(exc).__name__)
            return None

    def search_read(
        self,
        model: str,
        domain: list,
        fields: list,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order: Optional[str] = None,
    ) -> list:
        """Busca y lee registros en un solo paso."""
        kwargs: dict = {'fields': fields}
        if limit is not None:
            kwargs['limit'] = limit
        if offset is not None:
            kwargs['offset'] = offset
        if order:
            kwargs['order'] = order
        return self.execute_kw(model, 'search_read', [domain], kwargs) or []

    def read(self, model: str, ids: list, fields: list) -> list:
        """Lee registros específicos por sus IDs."""
        return self.execute_kw(model, 'read', [ids], {'fields': fields}) or []

    def search(
        self,
        model: str,
        domain: list,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        order: Optional[str] = None,
    ) -> list:
        """Busca registros y devuelve solo sus IDs."""
        kwargs: dict = {}
        if limit is not None:
            kwargs['limit'] = limit
        if offset is not None:
            kwargs['offset'] = offset
        if order:
            kwargs['order'] = order
        return self.execute_kw(model, 'search', [domain], kwargs) or []

    def search_count(self, model: str, domain: list) -> int:
        """Cuenta registros que coinciden con el domain sin traer los datos."""
        if not self.uid or not self.models:
            logger.warning("No hay conexion a Odoo disponible")
            return 0
        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'search_count', [domain]
            ) or 0
        except Exception as exc:
            logger.error("Error en search_count para %s: %s", model, type(exc).__name__)
            return 0

    def read_group(self, model: str, domain: list, fields: list, groupby: list) -> list:
        """Realiza consulta agregada (equivalente a GROUP BY en SQL)."""
        if not self.uid or not self.models:
            logger.warning("No hay conexion a Odoo disponible")
            return []
        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'read_group',
                [domain],
                {'fields': fields, 'groupby': groupby, 'lazy': False}
            ) or []
        except Exception as exc:
            logger.error("Error en read_group para %s: %s", model, type(exc).__name__)
            return []

    # ------------------------------------------------------------------
    # Paralelismo
    # ------------------------------------------------------------------

    def call_parallel(self, calls: List[dict]) -> list:
        """
        Ejecuta múltiples llamadas a Odoo en paralelo con ThreadPoolExecutor.

        Útil para consultas de enriquecimiento donde se buscan datos de modelos
        independientes (res.partner, account.account, sale.order, etc.) que no
        dependen entre sí. Reduce el tiempo total proporcional al nº de llamadas.

        Args:
            calls (list[dict]): Lista de especificaciones de llamada. Cada dict:
                - model  (str): Modelo de Odoo, ej: 'res.partner'
                - method (str): Método, ej: 'search_read', 'read', 'search_count'
                - args   (list): Argumentos posicionales
                - kwargs (dict, opcional): Argumentos con nombre

        Returns:
            list: Resultados en el mismo orden que `calls`. [] si una llamada falló.

        Ejemplo::

            moves, partners, accounts = repo.call_parallel([
                {'model': 'account.move',    'method': 'search_read',
                 'args': [domain],           'kwargs': {'fields': move_fields}},
                {'model': 'res.partner',     'method': 'read',
                 'args': [partner_ids],      'kwargs': {'fields': partner_fields}},
                {'model': 'account.account', 'method': 'read',
                 'args': [account_ids],      'kwargs': {'fields': account_fields}},
            ])
        """
        if not calls:
            return []

        results: list = [[] for _ in calls]

        def _execute(index: int, call: dict):
            try:
                result = self.models.execute_kw(
                    self.db, self.uid, self.password,
                    call['model'],
                    call['method'],
                    call.get('args', []),
                    call.get('kwargs', {}),
                )
                return index, result if result is not None else []
            except Exception as exc:
                logger.error(
                    "call_parallel[%d] %s.%s: %s",
                    index, call.get('model'), call.get('method'), type(exc).__name__
                )
                return index, []

        max_workers = min(len(calls), 8)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(_execute, i, c): i for i, c in enumerate(calls)}
            for future in as_completed(futures):
                idx, result = future.result()
                results[idx] = result

        return results
