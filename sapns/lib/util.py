# -*- coding: utf-8 -*-

import re
from sqlalchemy import Table
from sqlalchemy.exc import NoSuchTableError
from sqlalchemy.sql.expression import and_
from sqlalchemy.types import DATE, TIME, DATETIME, INTEGER, NUMERIC, \
    BOOLEAN, BIGINT
from sqlalchemy.schema import MetaData
from sapns.model import DBSession
from sapns.lib.dataset import DataSet

class Busqueda(object):
    
    def __init__(self, tabla, texto_busqueda, columnas_trans=None):
        self.tabla = tabla
        self.columnas = [col.name for col in self.tabla.columns]
        self.cache_campo = {}
        
        if not columnas_trans:
            self.columnas_trans = [re.sub(r'[^a-z0-9]*', '', self.quitar_acentos(col))
                                   for col in self.columnas]
        else:
            self.columnas_trans = columnas_trans        

        if texto_busqueda:
            self.condicion = self.condicion_busqueda(texto_busqueda)
            self.orden = self.orden_busqueda(texto_busqueda)
            
        else:
            self.condicion = self.orden = None

    def sin_acentos(self, texto):
        
        resultado = texto
        resultado = re.sub(r'(a|á)', '(a|á|ä)', resultado)
        resultado = re.sub(r'(e|é)', '(e|é|ë)', resultado)
        resultado = re.sub(r'(i|í)', '(i|í|ï)', resultado)
        resultado = re.sub(r'(o|ó)', '(o|ó|ö)', resultado)
        resultado = re.sub(r'(u|ú)', '(u|ú|ü)', resultado)
        
        return resultado
        
    def quitar_especiales(self, texto):
        texto = texto.encode('utf-8')
        
        return texto.\
            replace("'", "''").\
            replace('(', ' ').replace(')', ' ').\
            replace('?', ' ').replace('¿', ' ').\
            replace('@', ' ')
            
    def quitar_acentos(self, texto):
        texto = texto.encode('utf-8')
        
        return texto.lower().\
            replace('á', 'a').\
            replace('é', 'e').\
            replace('í', 'i').\
            replace('ó', 'o').\
            replace('ú', 'u').\
            replace('ü', 'u')
            
    def orden_busqueda(self, busqueda):
        terminos = busqueda.decode('utf-8').split(',')

        orden = []
        for termino in terminos:
            termino = termino.strip()
            if termino != '':
                m  = re.search(r'^(\+|-)(\w+)', termino)                
                if m is None:
                    continue
                
                operador = m.group(1)
                
                campos = termino.split(operador)
                
                c = self.get_col(campos[1].strip())
                if c:
                    if operador == '+':
                        operador = ' ASC'
                    elif operador == '-':
                        operador = ' DESC'
                        
                    orden.append('"%s" %s' % (c, operador))
                        
#        print 'ORDEN =' + '\n'.join(orden)
        return ', '.join(orden)
    
    def get_col(self, campo):
        
        if self.cache_campo.has_key(campo.lower()):
            return self.cache_campo[campo.lower()]
        
        else:
            col = None
            for ct, c in zip(self.columnas_trans, self.columnas):
                
                if ct.startswith(campo.lower()):
                    if not col or col['length'] > len(ct):
                        col = dict(name=c, length=len(ct))
                        
            if col:
                self.cache_campo[campo.lower()] = col['name']
                return col['name']
            
            else:
                return None
    
    def busqueda_campos(self, busqueda):
        
        terminos = busqueda.split(',')
        
        resultado = None
        sql = []
        for termino in terminos:
            termino = termino.strip()
            if termino != '':
                
                m = re.search(r'^(\w*)\s*(<>|<=|>=|==|=|<|>|#|!)(.+)', termino)                
                if m is None:
                    continue

                operador = m.group(2)
                campos = termino.split(operador)
                
                if operador == '#' or operador == '!':
                    campo = m.group(3).strip()
                    
                else:
                    campo = m.group(1).strip()
                    if m.group(3).strip() == '':
                        continue
                    
                c = self.get_col(campo)
                if not c:
                    continue
                
                col = self.tabla.columns[c]
                
                if operador in ['#', '!']:
                    
                    # fecha y hora
                    if isinstance(col.type, DATE) or \
                    isinstance(col.type, TIME) or \
                    isinstance(col.type, DATETIME):
                        # no es nulo
                        if operador == '#':
                            # "Fecha inicio" IS NOT NULL
                            sql.append('"%s" IS NOT NULL' % c.encode('utf-8'))
                            
                        # es nulo
                        elif operador == '!':
                            # "Fecha inicio" IS NULL
                            sql.append('"%s" IS NULL' % c.encode('utf-8'))

                        elif operador == '==':
                            sql.append('"%s" = \'%s\'' % (c.encode('utf-8'),
                                                          campos[1].strip()))

                    # números (integer, biginteger, numeric)
                    elif isinstance(col.type, INTEGER) or \
                    isinstance(col.type, NUMERIC) or \
                    isinstance(col.type, BIGINT):
                    
                        # no es nulo
                        if operador == '#':
                            # "Nº de alumnos" IS NOT NULL
                            sql.append('"%s" IS NOT NULL' % c.encode('utf-8'))
                            
                        # es nulo
                        elif operador == '!':
                            # "Nº de alumnos" IS NULL
                            sql.append('"%s" IS NULL' % c.encode('utf-8'))
                            
                        elif operador == '==':
                            # Nº de alumnos = 10
                            sql.append('"%s" = %s' % (c.encode('utf-8'),
                                                      campos[1].strip()))
                            
                    # booleano
                    elif isinstance(col.type, BOOLEAN):
                        
                        if operador == '#':
                            sql.append('"%s" = True' % c.encode('utf-8'))
                            
                        elif operador == '!':
                            sql.append('"%s" = False' % c.encode('utf-8'))                                         

                    # texto (o cualquier otra cosa)
                    else:
                        # no es nulo
                        if operador == '#':
                            # trim(coalesce("---" as Text), '')) <> ''
                            sql.append('TRIM(COALESCE(CAST("%s" as Text), \'\')) <> \'\'' % \
                                       c.encode('utf-8'))
                            
                        # es nulo
                        elif operador == '!':
                            # trim(coalesce("---" as Text), '')) = ''
                            sql.append('TRIM(COALESCE(CAST("%s" as Text), \'\')) = \'\'' % \
                                       c.encode('utf-8'))
                            
                        elif operador == '==':
                            sql.append('TRIM(COALESCE(CAST("%s" as Text), \'\')) = \'%s\'' % \
                                        (c.encode('utf-8'),
                                         campos[1]))                                         

                else:
                    explicitos = re.findall(r'"([^"]+)"', campos[1], re.I)
                    
                    # quitar los explícitos y los caracteres "especiales"
                    texto = self.quitar_especiales(re.sub(r'"[^"]+"', '', campos[1], re.I))
                    
                    terminos2 = texto.split()
                    expresiones = []
                    
                    expresion_novacio = 'TRIM(COALESCE(CAST("%s" as Text), \'\')) <> \'\'' % c.encode('utf-8')
                                               
                    for termino2 in terminos2:
                        termino2 = self.sin_acentos(termino2)
                        
                        # fecha, hora o fecha-hora
                        if isinstance(col.type, DATE) or \
                        isinstance(col.type, TIME) or \
                        isinstance(col.type, DATETIME):
                        
                            if operador in ['=', '<>']:
                                expresion_novacio = None
                                
                                # "Fecha inicio" = '01/01/2010'                   
                                expresion = '"%s" %s \'%s\'' % \
                                    (c.encode('utf-8'),
                                     operador.encode('utf-8'),
                                     termino2)
                                                
                            else:
                                # <, >, <=, >=
                                expresion_novacio = '"%s" IS NOT NULL' % c.encode('utf-8')
                                
                                # "Fecha inicio" >= '01/01/2010'
                                expresion = '"%s" %s \'%s\'' % \
                                    (c.encode('utf-8'), 
                                     operador.encode('utf-8'), 
                                     termino2)
                                    
                        # número
                        elif isinstance(col.type, INTEGER) or \
                        isinstance(col.type, NUMERIC) or \
                        isinstance(col.type, BIGINT):
                        
                            if operador in ['=', '<>']:
                                # "Nº de alumnos" = 10                   
                                expresion = '"%s" %s %s' % \
                                    (c.encode('utf-8'),
                                     operador.encode('utf-8'),
                                     termino2)
                                                
                            else:
                                # <, >, <=, >=
                                expresion_novacio = '"%s" IS NOT NULL' % c.encode('utf-8')
                                
                                # "Nº de alumnos" >= 10
                                expresion = '"%s" %s %s' % \
                                    (c.encode('utf-8'), 
                                     operador.encode('utf-8'), 
                                     termino2)

                        # texto (o cualquier otra cosa)
                        else: 
                            if operador == '=':                            
                                expresion = "UPPER(CAST(\"%s\" as Text)) SIMILAR TO UPPER('%%%s%%')" % \
                                                (c.encode('utf-8'), termino2)
                                                
                            elif operador == '<>':
                                expresion = "UPPER(CAST(\"%s\" as Text)) NOT SIMILAR TO UPPER('%%%s%%')" % \
                                                (c.encode('utf-8'), termino2)
                                                
                            else:
                                # <, >, <=, >=
                                expresion_novacio = '"%s" IS NOT NULL' % c.encode('utf-8')
                                
                                expresion = "\"%s\" %s '%s'" % \
                                    (c.encode('utf-8'), operador.encode('utf-8'), termino2)
                                        
                        expresiones.append(expresion)
                        
                    # explícitos ("---")
                    for exp in explicitos:
                        if operador == '=':                            
                            expresion = "UPPER(CAST(\"%s\" as Text)) LIKE UPPER('%%%s%%')" % \
                                            (c.encode('utf-8'), exp.encode('utf-8'))
                                            
                        elif operador == '<>':
                            expresion = "UPPER(CAST(\"%s\" as Text)) NOT LIKE UPPER('%%%s%%')" % \
                                            (c.encode('utf-8'), exp.encode('utf-8'))
                                            
                        expresiones.append(expresion)
                        
                    
                    expresion_novacio = ('%s AND \n(' % expresion_novacio 
                                         if expresion_novacio else '')
                    
                    if expresion_novacio:
                        sql.append('(' + expresion_novacio + ' AND\n'.join(expresiones) + '))')
                        
                    else:
                        sql.append('(' + ' AND\n'.join(expresiones) + ')')
                            
#        print 'SQL=' + '\n'.join(sql)
        if len(sql) > 0:
            resultado = ' AND\n'.join(sql).decode('utf-8')
        
        return resultado
                
    def condicion_busqueda(self, busqueda):
        
        if '*' in busqueda:
            sql = None
        
        else:            
            filtros = [f.replace("'", "''").strip() 
                       for f in busqueda.decode('utf-8').split(',')]
            
            sql = None
            sql_filtros = []
            for filtro in filtros:
                
                m = re.search(r'^([^"]*)(<>|<=|>=|==|=|<|>|#|!|\+|-)(.+)', filtro)  
                if m:
                    sql_filtro = self.busqueda_campos(filtro)
                    
                else:
                    sql_termino = []
                    
                    explicitos = re.findall(r'"([^"]+)"', filtro, re.I)
                    
                    filtro = re.sub(r'"[^"]+"', '', filtro, re.I | re.U)
                    
                    # quitar caracteres especiales
                    filtro = filtro.\
                        replace(u'(', u' ').replace(u')', u' ').\
                        replace(u'?', u' ').replace(u'¿', u' ').\
                        replace(u'@', u' ')
                    
                    terminos_de_busqueda = filtro.split()                    
                    
                    for termino in terminos_de_busqueda:
                                                
                        termino = self.sin_acentos(termino.encode('utf-8'))
                        
                        if termino.strip():
                            sql_campo = []
                            
                            for columna in self.columnas:
                                if columna != 'id' and columna != 'busqueda' and columna[0:3] != 'id_':
                                    try:
                                        texto = '(CAST("%s" as Text) <> \'\' AND ' % columna.encode('utf-8')
                                        texto += "UPPER(CAST(\"%s\" as Text)) SIMILAR TO UPPER('%%%s%%'))" % \
                                            (columna.encode('utf-8'), termino)
                                        
                                        sql_campo.append(texto)
                                    except:
                                        raise #return termino
                                
                            texto_sql_campo = ' OR\n'.join(sql_campo)
                            texto_sql_campo = ' (' + texto_sql_campo + ')'
                            
                            sql_termino.append(texto_sql_campo)
                    
                    # explícitos ("---")        
                    for exp in explicitos:
                        
                        termino = exp.encode('utf-8')
                        
                        if termino.strip():
                            sql_campo = []
                            
                            for columna in self.columnas:
                                if columna != 'id' and columna != 'busqueda' and columna[0:3] != 'id_':
                                    try:
                                        texto = '(CAST("%s" as Text) <> \'\' AND ' % columna.encode('utf-8')
                                        texto += "UPPER(CAST(\"%s\" as Text)) LIKE UPPER('%%%s%%'))" % \
                                            (columna.encode('utf-8'), termino)
                                        
                                        sql_campo.append(texto)
                                    except:
                                        raise #return termino
                                
                            texto_sql_campo = ' OR\n'.join(sql_campo)
                            texto_sql_campo = ' (' + texto_sql_campo + ')'
                            
                            sql_termino.append(texto_sql_campo)
                            
                    sql_filtro = ' AND\n'.join(sql_termino)
                    sql_filtro = sql_filtro.decode('utf-8')
                    
                if sql_filtro:
                    sql_filtros.append(sql_filtro)
                    
            if sql_filtros:
                sql = ' AND\n'.join(sql_filtros)
        
        return sql

def search(table_name, q=None, rp=100, offset=0):
    """
    """ 
    
    meta = MetaData(bind=DBSession.bind)
        
    try:
        tbl = Table(table_name, meta, autoload=True)
            
    except NoSuchTableError:
        raise
    
    sql = None
    orden = ''
    if search is not None:
        
        # procesar "busqueda"
        qres = Busqueda(tbl, q)
        
        # aplicar condiciones de búsqueda    
        sql = and_(qres.condicion, sql)
        #print(busq.condicion)
        
        # aplicar orden
        if qres.orden:
            orden = qres.orden
    
    # where
    qry = tbl.select(whereclause=sql)
    
    # order by
    if orden:
        qry = qry.order_by(orden)
        
    return DataSet.procesar_resultado(qry, rp, offset)