#!/usr/bin/env python
from tabulate import tabulate 
from danceschool.competitions.views import calculate_skating
    
judges_list = ['Jessy','Kuschi','Tanya','Kuva','Sondre']
data_dict = {
    'Oleksii & Vasilena': [ 4,6,4,4,3 ],
    'Alexander & Dona': [ 6,7,5,6,6 ],
    'Konstantin & Iliana': [ 7,5,6,7,7 ],
    'Serhii & Arkadiia': [ 1,2,2,3,1 ],
    'Martin & Viktoriia': [ 5,4,7,5,5 ],
    'Hristian & Anna': [ 3,1,3,2,4 ],
    'Niki & Iryna': [ 2,3,1,1,2 ],
}
sctable = calculate_skating(judges_list,data_dict)   
print(tabulate(sctable))

judges_list = ['j1','j2','j3']
data_dict = {
    'c1':[1,2,3],
    'c2':[2,3,1],
    'c3':[3,1,2],
    'c4':[4,4,4],
}
sctable = calculate_skating(judges_list,data_dict)   
print(tabulate(sctable))


