# -*- coding: utf-8 -*-
"""Create or update one BIM360 3D view for every non-empty Revit phase."""

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from Autodesk.Revit import DB
from System.Collections.Generic import List
from System.Drawing import Font, FontStyle, Point, Size
from System.Windows.Forms import (Button, ComboBox, ComboBoxStyle, DialogResult,
    DockStyle, Form, FormBorderStyle, FormStartPosition, HorizontalAlignment,
    Label, ListView, ListViewItem, MessageBox, MessageBoxButtons,
    MessageBoxIcon, View)

PREFERRED_PHASE_FILTER = "Current + Demo"
PREFERRED_CATEGORY_PARAMETER = "Category Name"
PREFERRED_SUBCATEGORY_PARAMETER = "Subcategory Name"
PREFERRED_VIEW_TEMPLATE = "Export BIM360"
VIEW_PREFIX = "BIM360 "
doc = __revit__.ActiveUIDocument.Document


class DataPresentation(object):
    def __init__(self, name, value):
        self.Name = name
        self.Value = value

    def __str__(self):
        return self.Name

    def __repr__(self):
        return self.Name


NONE_VALUE = DataPresentation("<None>", None)


class SelectionForm(Form):
    def __init__(self, phase_filters, view_parameters, view_templates):
        Form.__init__(self)
        self.Text = "SynSys : Create Export BIM360 Views"
        self.ClientSize = Size(520, 285)
        self.StartPosition = FormStartPosition.CenterScreen
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MinimizeBox = False
        self.MaximizeBox = False
        self.ShowIcon = False
        self.Font = Font("Segoe UI", 9, FontStyle.Regular)

        self.phase_filter_combo = self._add_combo(
            "Phase filter:", phase_filters, PREFERRED_PHASE_FILTER, 15)
        self.category_parameter_combo = self._add_combo(
            "Category parameter (value: Export):", view_parameters,
            PREFERRED_CATEGORY_PARAMETER, 70)
        self.subcategory_parameter_combo = self._add_combo(
            "Subcategory parameter (value: BIM360):", view_parameters,
            PREFERRED_SUBCATEGORY_PARAMETER, 125)
        self.view_template_combo = self._add_combo(
            "View template:", view_templates, PREFERRED_VIEW_TEMPLATE, 180)

        ok_button = Button()
        ok_button.Text = "Create / Update"
        ok_button.Location = Point(285, 240)
        ok_button.Size = Size(125, 28)
        ok_button.DialogResult = DialogResult.OK
        cancel_button = Button()
        cancel_button.Text = "Cancel"
        cancel_button.Location = Point(420, 240)
        cancel_button.Size = Size(80, 28)
        cancel_button.DialogResult = DialogResult.Cancel
        self.AcceptButton = ok_button
        self.CancelButton = cancel_button
        self.Controls.Add(ok_button)
        self.Controls.Add(cancel_button)

    def _add_combo(self, label_text, values, preferred_name, top):
        label = Label()
        label.Text = label_text
        label.Location = Point(20, top)
        label.Size = Size(480, 18)
        combo = ComboBox()
        combo.Location = Point(20, top + 20)
        combo.Size = Size(480, 24)
        combo.DropDownStyle = ComboBoxStyle.DropDownList
        for value in values:
            combo.Items.Add(value)
        combo.SelectedIndex = self._preferred_index(values, preferred_name)
        self.Controls.Add(label)
        self.Controls.Add(combo)
        return combo

    @staticmethod
    def _preferred_index(values, preferred_name):
        for index, value in enumerate(values):
            if value.Name == preferred_name:
                return index
        return 0


class ResultForm(Form):
    def __init__(self, rows):
        Form.__init__(self)
        self.Text = "BIM360 View Creation Result"
        self.ClientSize = Size(760, 520)
        self.MinimumSize = Size(600, 350)
        self.StartPosition = FormStartPosition.CenterScreen
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.ShowIcon = False
        self.Font = Font("Segoe UI", 9, FontStyle.Regular)
        table = ListView()
        table.Dock = DockStyle.Fill
        table.View = View.Details
        table.FullRowSelect = True
        table.GridLines = True
        table.Columns.Add("View / Phase", 260, HorizontalAlignment.Left)
        table.Columns.Add("Result", 470, HorizontalAlignment.Left)
        for name, status in rows:
            item = ListViewItem(name)
            item.SubItems.Add(status)
            table.Items.Add(item)
        close_button = Button()
        close_button.Text = "Close"
        close_button.Dock = DockStyle.Bottom
        close_button.Height = 30
        close_button.DialogResult = DialogResult.OK
        self.Controls.Add(table)
        self.Controls.Add(close_button)
        self.AcceptButton = close_button


def _presentation_items(elements):
    items = [DataPresentation(element.Name, element) for element in elements]
    items.append(NONE_VALUE)
    return sorted(items, key=lambda item: item.Name.lower())


def get_phase_filters():
    return _presentation_items(DB.FilteredElementCollector(doc).OfClass(DB.PhaseFilter))


def get_view_templates():
    views = DB.FilteredElementCollector(doc).OfClass(DB.View)
    return _presentation_items([view for view in views if view.IsTemplate])


def get_view_parameters():
    view_category = DB.Category.GetCategory(doc, DB.BuiltInCategory.OST_Views)
    definitions = []
    iterator = doc.ParameterBindings.ForwardIterator()
    while iterator.MoveNext():
        binding = iterator.Current
        if isinstance(binding, DB.ElementBinding):
            categories = binding.Categories
            if categories is not None and categories.Contains(view_category):
                definitions.append(iterator.Key)
    return _presentation_items(definitions)


def get_3d_view_type_id():
    for view_type in DB.FilteredElementCollector(doc).OfClass(DB.ViewFamilyType):
        if view_type.ViewFamily == DB.ViewFamily.ThreeDimensional:
            return view_type.Id
    return None


def get_3d_views_by_name():
    views = (DB.FilteredElementCollector(doc).OfClass(DB.View3D)
             .WhereElementIsNotElementType())
    return {view.Name: view for view in views if not view.IsTemplate}


def phase_has_elements(phase_id):
    statuses = List[DB.ElementOnPhaseStatus]()
    statuses.Add(DB.ElementOnPhaseStatus.New)
    statuses.Add(DB.ElementOnPhaseStatus.Demolished)
    statuses.Add(DB.ElementOnPhaseStatus.Temporary)
    phase_filter = DB.ElementPhaseStatusFilter(phase_id, statuses)
    return (DB.FilteredElementCollector(doc).WherePasses(phase_filter)
            .GetElementCount() > 0)


def _set_id_parameter(element, built_in_parameter, value, label):
    if value is None:
        return None
    parameter = element.get_Parameter(built_in_parameter)
    if parameter is None:
        return "{} not found".format(label)
    if parameter.IsReadOnly:
        return "{} is read-only".format(label)
    if not parameter.Set(value):
        return "Revit rejected {}".format(label)
    return None


def _set_text_parameter(element, parameter_name, value):
    if parameter_name is None:
        return None
    parameter = element.LookupParameter(parameter_name)
    if parameter is None:
        return "parameter '{}' not found".format(parameter_name)
    if parameter.IsReadOnly:
        return "parameter '{}' is read-only".format(parameter_name)
    if parameter.StorageType != DB.StorageType.String:
        return "parameter '{}' is not text".format(parameter_name)
    if not parameter.Set(value):
        return "Revit rejected parameter '{}'".format(parameter_name)
    return None


def configure_view(view, phase_id, phase_filter_id, category_name,
                   subcategory_name, template_id):
    results = (
        _set_id_parameter(view, DB.BuiltInParameter.VIEW_PHASE,
                          phase_id, "phase"),
        _set_id_parameter(view, DB.BuiltInParameter.VIEW_PHASE_FILTER,
                          phase_filter_id, "phase filter"),
        _set_text_parameter(view, category_name, "Export"),
        _set_text_parameter(view, subcategory_name, "BIM360"),
    )
    warnings = [result for result in results if result]
    if template_id is not None:
        try:
            view.ViewTemplateId = template_id
        except Exception as error:
            warnings.append("view template: {}".format(error))
    return warnings


def execute():
    form = SelectionForm(get_phase_filters(), get_view_parameters(),
                         get_view_templates())
    if form.ShowDialog() != DialogResult.OK:
        return

    phase_filter = form.phase_filter_combo.SelectedItem.Value
    category = form.category_parameter_combo.SelectedItem.Value
    subcategory = form.subcategory_parameter_combo.SelectedItem.Value
    template = form.view_template_combo.SelectedItem.Value
    phase_filter_id = phase_filter.Id if phase_filter is not None else None
    category_name = category.Name if category is not None else None
    subcategory_name = subcategory.Name if subcategory is not None else None
    template_id = template.Id if template is not None else None

    view_type_id = get_3d_view_type_id()
    if view_type_id is None:
        MessageBox.Show("No 3D view family type was found in the project.",
                        "Create BIM360 Views", MessageBoxButtons.OK,
                        MessageBoxIcon.Error)
        return

    existing_views = get_3d_views_by_name()
    processed_names = set()
    logs = []
    created_count = 0
    updated_count = 0
    transaction = DB.Transaction(doc, "SynSys : Create Export BIM360 Views")
    try:
        transaction.Start()
        for phase in doc.Phases:
            view_name = VIEW_PREFIX + phase.Name
            if not phase_has_elements(phase.Id):
                logs.append([phase.Name,
                    "No new, demolished, or temporary elements; view skipped."])
                continue
            view = existing_views.get(view_name)
            if view is None:
                view = DB.View3D.CreateIsometric(doc, view_type_id)
                view.Name = view_name
                action = "Created"
                created_count += 1
            else:
                action = "Updated"
                updated_count += 1
            warnings = configure_view(view, phase.Id, phase_filter_id,
                category_name, subcategory_name, template_id)
            processed_names.add(view_name)
            if warnings:
                action += "; warnings: " + "; ".join(warnings)
            logs.append([view_name, action])

        for view_name in existing_views:
            if view_name.startswith(VIEW_PREFIX) and view_name not in processed_names:
                logs.append([view_name,
                    "No matching non-empty phase; existing view was not changed."])
        status = transaction.Commit()
        if status != DB.TransactionStatus.Committed:
            raise Exception("Revit did not commit the transaction: {}".format(status))
    except Exception as error:
        if transaction.GetStatus() == DB.TransactionStatus.Started:
            transaction.RollBack()
        MessageBox.Show("No changes were saved.\n\n{}".format(error),
            "Create BIM360 Views Error", MessageBoxButtons.OK,
            MessageBoxIcon.Error)
        return

    logs.sort(key=lambda row: (row[1], row[0]))
    MessageBox.Show("Created: {}\nUpdated: {}".format(
        created_count, updated_count), "Create BIM360 Views",
        MessageBoxButtons.OK, MessageBoxIcon.Information)
    ResultForm(logs).ShowDialog()


if __name__ == "__main__":
    execute()
