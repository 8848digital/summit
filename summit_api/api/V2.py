import frappe
from summit_api.utils import success_response, error_response
import summit_api.api.v2.banner as banner
from summit_api.api.V1 import V1

class V2(V1):
    def __init__(self):
        self.methods = {'banner':['get']}

    def class_map(self,kwargs):
        entity = kwargs.get('entity')
        method = kwargs.get('method')
        if self.methods.get(entity) and method in self.methods.get(entity):
            function = f"{kwargs.get('entity')}.{kwargs.get('method')}({kwargs})"
            return eval(function)
        return V1.class_map(self,kwargs)

    
        
    
    
    