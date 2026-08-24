#-*- coding: utf-8 -*-

from Autodesk.Revit import DB
from Autodesk.Revit import UI
import sys
import os
from System.IO import StreamWriter
from rpw.ui.forms import select_folder

__title__ = "Check Parameter Bindings"
__doc__ = ""

doc = __revit__.ActiveUIDocument.Document
default_cats = ["Air Terminals","Casework","Ceilings","Columns","Communication Devices","Conduit Fittings","Conduits","Curtain Panels",
      "Curtain Wall Mullions","Data Devices","Doors","Duct Accessories","Duct Fittings","Ducts","Electrical Circuits","Electrical Equipment",
      "Electrical Fixtures","Fire Alarm Devices","Flex Ducts","Flex Pipes","Floors","Furniture","Generic Models","Lighting Devices",
      "Lighting Fixtures","Mechanical Equipment","Nurse Call Devices","Parking","Pipe Accessories","Pipe Fittings","Pipes","Plumbing Fixtures",
      "Railings","Roofs","Security Devices","Specialty Equipment","Sprinklers","Stairs","Structural Columns","Structural Foundations",
      "Structural Framing","Structural Trusses","Telephone Devices","Vertical Circulation","Walls","Windows"]

_s = ""

def check(parameter_name):
    global _s
    spes = DB.FilteredElementCollector(doc)\
        .OfClass(DB.SharedParameterElement)
    counter = 0
    for spe in spes:
        if spe.Name == parameter_name:
            counter += 1
            definition = spe.GetDefinition()
    if counter == 0:
        _s += "Параметр " + parameter_name + "не был найден в проекте" + "\n"
        UI.TaskDialog.Show("Title", "Параметр " + parameter_name + "не был найден в проекте")
    elif counter > 1:
        _s += "Параметр " + parameter_name + "больше, чем один" + "\n"
        UI.TaskDialog.Show("Title", "Параметр " + parameter_name + "больше, чем один")
    
    _cats = doc.ParameterBindings[definition].Categories
    cats = []
    for i in _cats:
        cats.append(i.Name)

    if len(cats) != len(default_cats):
        _s += "Количество параметров не совпадает" + "\n"
        UI.TaskDialog.Show("Title", "Количество параметров не совпадает")
    
    _t = ""
    for i in cats:
        if not i in default_cats:
            _t += i + "\n"
    if _t != "":
        _s += "Категории " + parameter_name + " отсутствуют в AMT \n" + _t + "\n"
        UI.TaskDialog.Show("Title", "Категории " + parameter_name + " отсутствуют в AMT \n" + _t)

    _t = ""
    for i in default_cats:
        if not i in cats:
            _t += i + "\n"
    if _t != "":
        _s += "Категории " + parameter_name + " отсутствуют в проекте \n" + _t + "\n"
        UI.TaskDialog.Show("Title", "Категории " + parameter_name + " отсутствуют в проекте \n" + _t)

def save_string(string):
    path = select_folder()
    filepath = os.path.join(path, doc.Title + " - parameters" + ".txt")
    sw = StreamWriter(filepath)
    sw.WriteLine(string)
    sw.Close()


for i in ["Instance Name", "Type Name"]:
    check(i)

save_string(_s)