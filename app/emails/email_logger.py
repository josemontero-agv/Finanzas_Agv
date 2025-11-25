# -*- coding: utf-8 -*-
"""
Módulo de Logging para Auditoría de Envíos de Correos.

Sistema simple de logging usando SQLite para registrar todos los envíos de correos.
"""

import sqlite3
import os
from datetime import datetime
from pathlib import Path


class EmailLogger:
    """
    Logger simple para auditoría de envíos de correos.
    """
    
    def __init__(self, db_path=None):
        """
        Inicializa el logger.
        
        Args:
            db_path (str, optional): Ruta al archivo SQLite. 
                                     Si es None, usa 'logs/email_audit.db' en el directorio del proyecto.
        """
        if db_path is None:
            # Crear directorio logs si no existe
            project_root = Path(__file__).parent.parent.parent
            logs_dir = project_root / 'logs'
            logs_dir.mkdir(exist_ok=True)
            db_path = logs_dir / 'email_audit.db'
        
        self.db_path = str(db_path)
        self._init_database()
    
    def _init_database(self):
        """Inicializa la base de datos SQLite con la tabla de logs."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS email_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                recipient_email TEXT NOT NULL,
                recipient_name TEXT,
                subject TEXT NOT NULL,
                letter_count INTEGER NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                letter_ids TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Índice para búsquedas rápidas por fecha y email
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp ON email_logs(timestamp)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_email ON email_logs(recipient_email)
        ''')
        
        conn.commit()
        conn.close()
    
    def log_email_sent(self, recipient_email, recipient_name, subject, letter_count, letter_ids=None):
        """
        Registra un envío exitoso de correo.
        
        Args:
            recipient_email (str): Email del destinatario
            recipient_name (str): Nombre del destinatario
            subject (str): Asunto del correo
            letter_count (int): Cantidad de letras incluidas
            letter_ids (list, optional): IDs de las letras enviadas
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        letter_ids_str = ','.join(map(str, letter_ids)) if letter_ids else None
        
        cursor.execute('''
            INSERT INTO email_logs 
            (timestamp, recipient_email, recipient_name, subject, letter_count, status, letter_ids)
            VALUES (?, ?, ?, ?, ?, 'sent', ?)
        ''', (
            datetime.now().isoformat(),
            recipient_email,
            recipient_name,
            subject,
            letter_count,
            letter_ids_str
        ))
        
        conn.commit()
        conn.close()
    
    def log_email_failed(self, recipient_email, recipient_name, subject, error_message, letter_ids=None):
        """
        Registra un fallo en el envío de correo.
        
        Args:
            recipient_email (str): Email del destinatario
            recipient_name (str): Nombre del destinatario
            subject (str): Asunto del correo
            error_message (str): Mensaje de error
            letter_ids (list, optional): IDs de las letras que se intentaron enviar
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        letter_ids_str = ','.join(map(str, letter_ids)) if letter_ids else None
        
        cursor.execute('''
            INSERT INTO email_logs 
            (timestamp, recipient_email, recipient_name, subject, letter_count, status, error_message, letter_ids)
            VALUES (?, ?, ?, ?, ?, 'failed', ?, ?)
        ''', (
            datetime.now().isoformat(),
            recipient_email,
            recipient_name,
            subject,
            len(letter_ids) if letter_ids else 0,
            error_message,
            letter_ids_str
        ))
        
        conn.commit()
        conn.close()
    
    def get_logs(self, start_date=None, end_date=None, recipient_email=None, limit=100):
        """
        Obtiene logs de envíos.
        
        Args:
            start_date (str, optional): Fecha inicial (YYYY-MM-DD)
            end_date (str, optional): Fecha final (YYYY-MM-DD)
            recipient_email (str, optional): Filtrar por email
            limit (int): Límite de registros (default: 100)
        
        Returns:
            list: Lista de diccionarios con los logs
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = 'SELECT * FROM email_logs WHERE 1=1'
        params = []
        
        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND timestamp <= ?'
            params.append(end_date + ' 23:59:59')
        
        if recipient_email:
            query += ' AND recipient_email = ?'
            params.append(recipient_email)
        
        query += ' ORDER BY timestamp DESC LIMIT ?'
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_stats(self, start_date=None, end_date=None):
        """
        Obtiene estadísticas de envíos.
        
        Args:
            start_date (str, optional): Fecha inicial (YYYY-MM-DD)
            end_date (str, optional): Fecha final (YYYY-MM-DD)
        
        Returns:
            dict: Estadísticas (total_sent, total_failed, total_emails, total_letters)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = 'SELECT status, COUNT(*) as count, SUM(letter_count) as total_letters FROM email_logs WHERE 1=1'
        params = []
        
        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date)
        
        if end_date:
            query += ' AND timestamp <= ?'
            params.append(end_date + ' 23:59:59')
        
        query += ' GROUP BY status'
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        stats = {
            'total_sent': 0,
            'total_failed': 0,
            'total_emails': 0,
            'total_letters': 0
        }
        
        for row in rows:
            status, count, letters = row
            stats['total_emails'] += count
            stats['total_letters'] += letters or 0
            if status == 'sent':
                stats['total_sent'] = count
            elif status == 'failed':
                stats['total_failed'] = count
        
        conn.close()
        return stats

