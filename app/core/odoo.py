# -*- coding: utf-8 -*-
"""
Repositorio de conexión a Odoo.

Maneja la conexión XML-RPC y autenticación con Odoo.
Patrón Repository para abstraer el acceso a datos de Odoo.
"""

import xmlrpc.client


class OdooRepository:
    """
    Repositorio para conexión a Odoo usando XML-RPC.
    
    Abstrae el acceso a datos de Odoo y proporciona métodos convenientes
    para búsqueda y lectura de registros.
    """
    
    def __init__(self, url, db, username, password):
        """
        Inicializa la conexión a Odoo.
        
        Args:
            url (str): URL del servidor Odoo (ej: 'https://odoo.example.com')
            db (str): Nombre de la base de datos
            username (str): Usuario de Odoo
            password (str): Contraseña del usuario
        """
        self.url = url
        self.db = db
        self.username = username
        self.password = password
        self.uid = None
        self.models = None
        
        # Validar que todas las credenciales estén configuradas
        if not all([self.url, self.db, self.username, self.password]):
            raise ValueError("Faltan credenciales de Odoo. Se requieren: url, db, username, password")
        
        # Establecer conexión
        self._connect()
    
    def _connect(self):
        """Establece la conexión con Odoo."""
        try:
            # Conectar al endpoint común de autenticación
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            
            # Autenticar
            self.uid = common.authenticate(self.db, self.username, self.password, {})
            
            if self.uid:
                # Conectar al endpoint de modelos
                self.models = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/object')
                print("[OK] Conexión a Odoo establecida exitosamente.")
            else:
                print("[ERROR] No se pudo autenticar. Credenciales inválidas.")
                self.uid = None
                self.models = None
                
        except Exception as e:
            print(f"[ERROR] Error en la conexión a Odoo: {e}")
            print("[INFO] Continuando sin conexión a Odoo.")
            self.uid = None
            self.models = None
    
    def authenticate_user(self, username, password):
        """
        Autentica un usuario contra Odoo.
        
        Args:
            username (str): Nombre de usuario
            password (str): Contraseña
        
        Returns:
            bool: True si la autenticación fue exitosa
        """
        try:
            # Crear conexión temporal para autenticación
            common = xmlrpc.client.ServerProxy(f'{self.url}/xmlrpc/2/common')
            
            # Intentar autenticar con las credenciales proporcionadas
            uid = common.authenticate(self.db, username, password, {})
            
            if uid:
                print(f"[OK] Autenticación exitosa para usuario: {username}")
                return True
            else:
                print(f"[ERROR] Credenciales incorrectas para usuario: {username}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Error en autenticación contra Odoo: {e}")
            
            # Fallback: verificar si las credenciales coinciden con las del repositorio
            try:
                if username == self.username and password == self.password:
                    print(f"[OK] Autenticación exitosa usando credenciales del repositorio")
                    return True
                else:
                    print(f"[ERROR] Credenciales no coinciden con las configuradas")
                    return False
            except Exception as fallback_error:
                print(f"[ERROR] Error en fallback de autenticación: {fallback_error}")
                return False
    
    def execute_kw(self, model, method, args, kwargs=None):
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
            print("[WARN] No hay conexión a Odoo disponible")
            return None
        
        if kwargs is None:
            kwargs = {}
        
        try:
            return self.models.execute_kw(
                self.db, self.uid, self.password,
                model, method, args, kwargs
            )
        except Exception as e:
            print(f"[ERROR] Error ejecutando {model}.{method}: {e}")
            return None
    
    def search_read(self, model, domain, fields, limit=None, offset=None, order=None):
        """
        Método conveniente para search_read.
        
        Busca y lee registros en un solo paso.
        
        Args:
            model (str): Modelo de Odoo
            domain (list): Dominio de búsqueda (filtros)
            fields (list): Campos a obtener
            limit (int, optional): Límite de registros
            offset (int, optional): Offset para paginación
            order (str, optional): Campo de ordenamiento
        
        Returns:
            list: Registros encontrados
        """
        options = {'fields': fields}
        if limit:
            options['limit'] = limit
        if offset:
            options['offset'] = offset
        if order:
            options['order'] = order
        
        return self.execute_kw(model, 'search_read', [domain], options) or []
    
    def read(self, model, ids, fields):
        """
        Método conveniente para read.
        
        Lee registros específicos por sus IDs.
        
        Args:
            model (str): Modelo de Odoo
            ids (list): IDs de registros a leer
            fields (list): Campos a obtener
        
        Returns:
            list: Registros leídos
        """
        return self.execute_kw(model, 'read', [ids], {'fields': fields}) or []
    
    def search(self, model, domain, limit=None, offset=None, order=None):
        """
        Método conveniente para search.
        
        Busca registros y devuelve solo sus IDs.
        
        Args:
            model (str): Modelo de Odoo
            domain (list): Dominio de búsqueda (filtros)
            limit (int, optional): Límite de registros
            offset (int, optional): Offset para paginación
            order (str, optional): Campo de ordenamiento
        
        Returns:
            list: IDs de registros encontrados
        """
        options = {}
        if limit:
            options['limit'] = limit
        if offset:
            options['offset'] = offset
        if order:
            options['order'] = order
        
        return self.execute_kw(model, 'search', [domain], options) or []
    
    def is_connected(self):
        """
        Verifica si hay conexión activa a Odoo.
        
        Returns:
            bool: True si está conectado
        """
        return bool(self.uid and self.models)
    
    def search_count(self, model, domain):
        """
        Cuenta registros que coinciden con el domain sin traer los datos.
        Optimizado para paginación y estadísticas.
        
        Args:
            model (str): Nombre del modelo de Odoo
            domain (list): Domain de búsqueda (filtros)
        
        Returns:
            int: Cantidad de registros que coinciden con el domain
        """
        if not self.uid or not self.models:
            print("[WARN] No hay conexión a Odoo disponible")
            return 0
        
        try:
            count = self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'search_count', [domain]
            )
            return count
        except Exception as e:
            print(f"[ERROR] Error en search_count para {model}: {e}")
            return 0
    
    def read_group(self, model, domain, fields, groupby):
        """
        Realiza consulta agregada en Odoo (equivalente a GROUP BY en SQL).
        Permite obtener sumas, promedios y conteos sin traer todos los registros.
        
        Args:
            model (str): Nombre del modelo de Odoo
            domain (list): Filtros de búsqueda
            fields (list): Campos a agregar (ej: ['amount_total', 'amount_residual'])
            groupby (list): Campos para agrupar ([] para agregación total)
        
        Returns:
            list: Resultados agregados. Ej: [{'amount_total': 50000, '__count': 100}]
        """
        if not self.uid or not self.models:
            print("[WARN] No hay conexión a Odoo disponible")
            return []
        
        try:
            result = self.models.execute_kw(
                self.db, self.uid, self.password,
                model, 'read_group',
                [domain],
                {
                    'fields': fields,
                    'groupby': groupby,
                    'lazy': False
                }
            )
            return result
        except Exception as e:
            print(f"[ERROR] Error en read_group para {model}: {e}")
            return []

