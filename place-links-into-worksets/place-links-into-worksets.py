# -*- coding: utf-8 -*-

import clr

clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Drawing import ContentAlignment, Font, FontStyle, Point, Size
from System.Windows.Forms import (
    Button,
    DialogResult,
    DockStyle,
    Form,
    FormBorderStyle,
    FormStartPosition,
    HorizontalAlignment,
    Label,
    ListView,
    ListViewItem,
    Padding,
    TextBox,
    View,
)

from Autodesk.Revit import DB


class _abstract_form(Form):

    def __init__(self):
        Form.__init__(self)
        self.StartPosition = FormStartPosition.CenterScreen
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MinimizeBox = False
        self.MaximizeBox = False
        self.ShowIcon = False
        self.Font = Font("Segoe UI", 9, FontStyle.Regular)
        self.Padding = Padding(15)


class message_box(_abstract_form):

    def __init__(self, text, title="Warning!"):
        _abstract_form.__init__(self)
        self._text = text
        self._title = title
        self._init_comp()

    def _init_comp(self):
        self.ClientSize = Size(400, 160)
        self.Text = self._title

        self._label = Label()
        self._label.Text = self._text
        self._label.Dock = DockStyle.Fill
        self._label.TextAlign = ContentAlignment.MiddleCenter

        self._button = Button()
        self._button.Text = "OK"
        self._button.Dock = DockStyle.Bottom
        self._button.Height = 30
        self._button.Click += self._button_click

        self.Controls.Add(self._label)
        self.Controls.Add(self._button)

    def _button_click(self, sender, event):
        self.Close()


class entering_values(_abstract_form):

    def __init__(self):
        _abstract_form.__init__(self)
        self.value = "Link "
        self._init_comp()

    def _init_comp(self):
        self.ClientSize = Size(400, 115)
        self.Text = "SynSys : Entering Value"

        self._label = Label()
        self._label.Text = "Enter a prefix for the created worksets:"
        self._label.Location = Point(10, 10)
        self._label.AutoSize = True

        self._textbox = TextBox()
        self._textbox.Location = Point(10, 35)
        self._textbox.Width = 360
        self._textbox.Text = self.value

        self._ok_button = Button()
        self._ok_button.Text = "OK"
        self._ok_button.Location = Point(205, 75)
        self._ok_button.Click += self._ok_clicked

        self._cancel_button = Button()
        self._cancel_button.Text = "Cancel"
        self._cancel_button.Location = Point(295, 75)
        self._cancel_button.Click += self._cancel_clicked

        self.AcceptButton = self._ok_button
        self.CancelButton = self._cancel_button
        self.Controls.Add(self._label)
        self.Controls.Add(self._textbox)
        self.Controls.Add(self._ok_button)
        self.Controls.Add(self._cancel_button)

    def _ok_clicked(self, sender, event):
        self.value = self._textbox.Text
        self.DialogResult = DialogResult.OK
        self.Close()

    def _cancel_clicked(self, sender, event):
        self.DialogResult = DialogResult.Cancel
        self.Close()


class link_table(_abstract_form):

    def __init__(self, data):
        _abstract_form.__init__(self)
        self._data = data
        self._init_comp()

    def _init_comp(self):
        self.ClientSize = Size(600, 560)
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.MinimumSize = Size(500, 350)
        self.Text = "Link Placement Result"

        self._list_view = ListView()
        self._list_view.Dock = DockStyle.Fill
        self._list_view.View = View.Details
        self._list_view.FullRowSelect = True
        self._list_view.GridLines = True
        self._list_view.Columns.Add(
            "Revit File", 220, HorizontalAlignment.Left
        )
        self._list_view.Columns.Add(
            "Status", 340, HorizontalAlignment.Left
        )

        for row in self._data:
            item = ListViewItem(row[0])
            item.SubItems.Add(row[1])
            self._list_view.Items.Add(item)

        self._button = Button()
        self._button.Text = "Close"
        self._button.Dock = DockStyle.Bottom
        self._button.Height = 30
        self._button.Click += self._button_click

        self.Controls.Add(self._list_view)
        self.Controls.Add(self._button)

    def _button_click(self, sender, event):
        self.Close()


def _element_id_value(element_id):
    """Return an integer value for ElementId in old and new Revit versions."""
    if hasattr(element_id, "Value"):
        return element_id.Value
    return element_id.IntegerValue


def _same_element_id(first_id, second_id):
    if first_id is None or second_id is None:
        return False
    return _element_id_value(first_id) == _element_id_value(second_id)


def _link_name(link_type):
    """Get a stable link type name without relying on instance-name formatting."""
    name_parameter = link_type.get_Parameter(
        DB.BuiltInParameter.SYMBOL_NAME_PARAM
    )
    if name_parameter is not None:
        name = name_parameter.AsString()
        if name:
            return name.strip()

    try:
        return link_type.Name.strip()
    except Exception:
        return ""


def _name_without_rvt_extension(name):
    trimmed_name = name.strip()
    if trimmed_name.lower().endswith(".rvt"):
        return trimmed_name[:-4].rstrip()
    return trimmed_name


def _workset_name_error(name):
    if not name or not name.strip():
        return "The workset name is empty"
    if len(name) > 255:
        return "The workset name is longer than 255 characters"

    invalid_characters = '\\:{}[]|;<>?`~'
    used_characters = [character for character in invalid_characters
                       if character in name]
    if used_characters:
        return "The workset name contains invalid characters: " + \
            " ".join(used_characters)
    return None


def _set_workset_parameter(element, workset_id):
    if element is None:
        return "Element was not found"

    try:
        parameter = element.get_Parameter(
            DB.BuiltInParameter.ELEM_PARTITION_PARAM
        )
        if parameter is None:
            return "The Workset parameter was not found"
        if parameter.IsReadOnly:
            return "The Workset parameter is read-only"

        workset_id_value = _element_id_value(workset_id)
        if parameter.StorageType == DB.StorageType.Integer:
            if parameter.AsInteger() == workset_id_value:
                return None
            result = parameter.Set(int(workset_id_value))
        elif parameter.StorageType == DB.StorageType.ElementId:
            if _same_element_id(parameter.AsElementId(), workset_id):
                return None
            result = parameter.Set(workset_id)
        else:
            return "The Workset parameter has an unexpected storage type"

        if not result:
            return "Revit rejected the Workset parameter value"
    except Exception as error:
        return str(error)
    return None


doc = __revit__.ActiveUIDocument.Document
state = True

if not doc.IsWorkshared:
    message_box(
        "This document does not include collaboration functionality. "
        "Enable worksharing and create worksets before running the plugin."
    ).ShowDialog()
    state = False

if state:
    entering_value = entering_values()
    entering_value.ShowDialog()
    if entering_value.DialogResult == DialogResult.OK:
        prefix = entering_value.value
    else:
        state = False

if state:
    link_instances = list(
        DB.FilteredElementCollector(doc)
        .OfClass(DB.RevitLinkInstance)
        .WhereElementIsNotElementType()
        .ToElements()
    )

    if not link_instances:
        message_box(
            "No Revit link instances were found in the current document.",
            "Link Placement Result",
        ).ShowDialog()
        state = False

if state:
    worksets = (
        DB.FilteredWorksetCollector(doc)
        .OfKind(DB.WorksetKind.UserWorkset)
        .ToWorksets()
    )
    worksets_by_name = {
        workset.Name.lower(): workset.Id for workset in worksets
    }

    links_by_type = {}
    logs = []
    for link_instance in link_instances:
        type_id = link_instance.GetTypeId()
        type_key = _element_id_value(type_id)
        if type_key not in links_by_type:
            links_by_type[type_key] = {
                "type": doc.GetElement(type_id),
                "instances": [],
            }
        links_by_type[type_key]["instances"].append(link_instance)

    transaction = DB.Transaction(
        doc, "SynSys : Place Links Into Worksets"
    )

    try:
        transaction.Start()

        for link_data in links_by_type.values():
            link_type = link_data["type"]
            file_name = _link_name(link_type)
            link_name = _name_without_rvt_extension(file_name)
            display_name = file_name or "Unknown Revit link"

            if getattr(link_type, "IsNestedLink", False):
                logs.append([display_name, "Skipped nested Revit link"])
                continue

            workset_name = prefix + link_name

            validation_error = _workset_name_error(workset_name)
            if validation_error:
                logs.append([display_name, "Error: " + validation_error])
                continue

            workset_key = workset_name.lower()
            workset_id = worksets_by_name.get(workset_key)
            workset_created = False

            if workset_id is None:
                try:
                    new_workset = DB.Workset.Create(doc, workset_name)
                    workset_id = new_workset.Id
                    worksets_by_name[workset_key] = workset_id
                    workset_created = True
                except Exception as error:
                    logs.append([
                        display_name,
                        "Error creating workset: " + str(error),
                    ])
                    continue

            errors = []
            type_error = _set_workset_parameter(link_type, workset_id)
            if type_error:
                errors.append("link type: " + type_error)

            for link_instance in link_data["instances"]:
                instance_error = _set_workset_parameter(
                    link_instance, workset_id
                )
                if instance_error:
                    errors.append(
                        "instance {0}: {1}".format(
                            _element_id_value(link_instance.Id),
                            instance_error,
                        )
                    )

            if errors:
                logs.append([display_name, "Error: " + "; ".join(errors)])
            elif workset_created:
                logs.append([
                    display_name,
                    "Created and assigned workset " + workset_name,
                ])
            else:
                logs.append([
                    display_name,
                    "Assigned existing workset " + workset_name,
                ])

        commit_status = transaction.Commit()
        if commit_status != DB.TransactionStatus.Committed:
            raise Exception(
                "Revit did not commit the transaction: " + str(commit_status)
            )
    except Exception as error:
        if transaction.GetStatus() == DB.TransactionStatus.Started:
            transaction.RollBack()
        message_box(
            "No changes were saved.\n\n" + str(error),
            "Link Placement Error",
        ).ShowDialog()
        state = False

    if state:
        link_table(logs).ShowDialog()
