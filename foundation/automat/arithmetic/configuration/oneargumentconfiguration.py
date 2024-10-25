FUNC_NAMES = {
    "sin":{
        'class_name':'Sine',
        'reverse_prefix':'arc',
        'import':['from math import sin'],
        'code':['num=sin(v0)'],
        'reverse_import':['from math import asin'],
        'reverse_code':['num=asin(v0)']
    },
    "cos":{
        'class_name':'Cosine',
        'reverse_prefix':'arc',
        'import':['from math import cos'],
        'code':['num=cos(v0)'],
        'reverse_import':['from math import acos'],
        'reverse_code':['num=acos(v0)']
    },
    "tan":{
        'class_name':'Tangent',
        'reverse_prefix':'arc',
        'import':['from math import tan'],
        'code':['num=tan(v0)'],
        'reverse_import':['from math import atan'],
        'reverse_code':['num=atan(v0)']
    },
    "sec":{
        'class_name':'Secant',
        'reverse_prefix':'arc',
        'import':['from math import sin'],
        'code':['num=1.0/sin(v0)'],
        'reverse_import':['from math import asin'],
        'reverse_code':['num=1.0/asin(v0)']
    },
    "cosec":{
        'class_name':'Cosecant',
        'reverse_prefix':'arc',
        'import':['from math import cos'],
        'code':['num=1.0/cos(v0)'],
        'reverse_import':['from math import acos'],
        'reverse_code':['num=1.0/acos(v0)']
    },
    "cot":{
        'class_name':'Cotangent',
        'reverse_prefix':'arc',
        'import':['from math import tan'],
        'code':['num=1.0/tan(v0)'],
        'reverse_import':['from math import atan'],
        'reverse_code':['num=1.0/atan(v0)']
    },
    ####Hyperbolic Trigonometric functions

    "sinh":{
        'class_name':'Sineh',
        'reverse_prefix':'arc',
        'import':['from math import sinh'],
        'code':['num=sinh(v0)'],
        'reverse_import':['from math import asinh'],
        'reverse_code':['num=asinh(v0)']
    },
    "cosh":{
        'class_name':'Cosineh',
        'reverse_prefix':'arc',
        'import':['from math import cosh'],
        'code':['num=cosh(v0)'],
        'reverse_import':['from math import acosh'],
        'reverse_code':['num=acosh(v0)']
    },
    "tanh":{
        'class_name':'Tangenth',
        'reverse_prefix':'arc',
        'import':['from math import tanh'],
        'code':['num=tanh(v0)'],
        'reverse_import':['from math import atanh'],
        'reverse_code':['num=atanh(v0)']
    },
    "sech":{
        'class_name':'Secanth',
        'reverse_prefix':'arc',
        'import':['from math import sinh'],
        'code':['num=1.0/sinh(v0)'],
        'reverse_import':['from math import asinh'],
        'reverse_code':['num=1.0/asinh(v0)']
    },
    "cosech":{
        'class_name':'Cosecanth',
        'reverse_prefix':'arc',
        'import':['from math import cosh'],
        'code':['num=1.0/cosh(v0)'],
        'reverse_import':['from math import acosh'],
        'reverse_code':['num=1.0/acosh(v0)']
    },
    "coth":{
        'class_name':'Cotangenth',
        'reverse_prefix':'arc',
        'import':['from math import tanh'],
        'code':['num=1.0/tanh(v0)'],
        'reverse_import':['from math import atanh'],
        'reverse_code':['num=1.0/atanh(v0)']
    },
}