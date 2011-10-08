# -*- coding: utf-8 -*-

from executor import Executor
    
if __name__ == '__main__':
    
    e = Executor()
    e.execute('sapns.exc.example.example', 'test1')
    e.execute('sapns.exc.example.example', 'test2', 100, 200, three=300)
    e.execute('sapns.exc.example.example', 'Test', 101, 202, three=303)
