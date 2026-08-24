#-*- coding: utf-8 -*-

from Autodesk.Revit import DB
from Autodesk.Revit import UI
from System.IO import StreamWriter
from rpw.ui.forms import select_folder
import os

__title__ = "Get All Elements\nWithout Geometry"
__doc__ = ""

doc = __revit__.ActiveUIDocument.Document

opt = DB.Options()
opt.DetailLevel = DB.ViewDetailLevel.Fine

def get_elements():
    elements = DB.FilteredElementCollector(doc)\
        .WhereElementIsNotElementType()\
        .ToElements()
    return elements

def get_elements_without_geometry(element, except_categories = []):
    geo = element.get_Geometry(opt)
    if element.Category == None or geo == None:
        return None
    elif element.Category.CategoryType != DB.CategoryType.Model:
        return None
    elif str(element.Category.Name) in except_categories: # ["Center line", "Center Line", "Cameras", "Legend Components", "Lines"]
        return None
    else:
        enum = geo.GetEnumerator()
        t = 0
        while enum.MoveNext():
            g = enum.Current
            if isinstance(g, DB.GeometryInstance):
                solids = g.GetInstanceGeometry()
                for i in solids:
                    if isinstance(i, DB.Solid):
                        t += i.Volume
            elif isinstance(g, DB.Solid):
                t += g.Volume
        if t == 0:
            return True
        else:
            return False

def save_string(string, path):
    sw = StreamWriter(path)
    sw.WriteLine(string)
    sw.Close()

elements = get_elements()
strong = ""
for element in elements:
    if get_elements_without_geometry(element, ["Center line", "Center Line", "Cameras", "Legend Components", "Lines"]):
        try:
            strong += element.Name + "\t" + element.Category.Name + "\t" + str(element.Id) + '\n'
        except:
            print(element.Category.Name + "\t" + str(element.Id))
path = select_folder()
filepath = os.path.join(path, doc.Title + ".txt")
save_string(strong, filepath)


UI.TaskDialog.Show("Title", "Gotovo!")