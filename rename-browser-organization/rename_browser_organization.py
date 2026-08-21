# -*- coding: utf-8 -*-

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")
from System.Windows.Forms import (
    Button,
    ColumnStyle,
    DataGridView,
    DataGridViewAutoSizeColumnsMode,
    DataGridViewTextBoxColumn,
    DockStyle,
    Form,
    FormBorderStyle,
    FormStartPosition,
    Label,
    MessageBox,
    MessageBoxButtons,
    MessageBoxIcon,
    Padding,
    RowStyle,
    SizeType,
    TableLayoutPanel,
)
from System.Drawing import Font, FontStyle, Size

from Autodesk.Revit.DB import (
    BrowserOrganization,
    FilteredElementCollector,
    Transaction,
)

class MainWindows(Form):
    def __init__(self):

        #
        self.is_not_cancel = False
        self.filled_rows = []

        #
        start_size_width, start_size_height = 700, 900
        const_for_min_size = 200

        #
        self.StartPosition = FormStartPosition.CenterScreen
        self.Size = Size(start_size_width,
                         start_size_height)
        self.MinimumSize = Size(start_size_width - const_for_min_size,
                                start_size_height - const_for_min_size)
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.MinimizeBox = False
        self.ShowIcon = False
        self.Text = "Rename Browser Organisation"
        self.Font = Font("Segoe UI", 9, FontStyle.Regular)

        #
        self._init_comp()

    def _init_comp(self):

        # table_lp1
        self.table_lp1 = TableLayoutPanel()
        self.table_lp1.Dock = DockStyle.Fill

        self.table_lp1.ColumnCount = 1
        self.table_lp1.RowCount = 3
        self.table_lp1.RowStyles.Add(RowStyle(SizeType.Absolute, 50))
        self.table_lp1.RowStyles.Add(RowStyle(SizeType.Percent, 90))
        self.table_lp1.RowStyles.Add(RowStyle(SizeType.Absolute, 50))
        self.table_lp1.Padding = Padding(15)

        # table_lp2
        self.table_lp2 = TableLayoutPanel()
        self.table_lp2.Dock = DockStyle.Fill

        self.table_lp2.ColumnCount = 2
        self.table_lp2.RowCount = 1
        self.table_lp2.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 75))
        self.table_lp2.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 25))

        # data_gv
        self.data_gv = DataGridView()
        self.data_gv.Dock = DockStyle.Fill
        
        self.data_gv.AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill
        self.data_gv.AllowUserToAddRows = False
        self.data_gv.AllowUserToDeleteRows = False
        self.data_gv.RowHeadersVisible = False
        self.data_gv.ColumnHeadersHeight = 50

        MainWindows._create_columns(
            (("Id", True),
             ("Type", True),
             ("Name", True),
             ("New Name", False)),
             self.data_gv)

        # rename_btn
        self.rename_btn = Button()
        self.rename_btn.Dock = DockStyle.Fill
        self.rename_btn.Text = "Rename"
        self.rename_btn.Click += self._get_filled_rows

        # cancel_btn
        self.cancel_btn = Button()
        self.cancel_btn.Dock = DockStyle.Fill
        self.cancel_btn.Text = "Cancel"
        self.cancel_btn.Click += self._cancel_action

        # text_label
        self.text_label = Label()
        self.text_label.Dock = DockStyle.Fill
        self.text_label.Text = (
            "This script renames built-in browser organizations. "
            "It is useful when the project language changes but the organization names remain unchanged."
        )
        
        # adding controls
        self.table_lp2.Controls.Add(self.rename_btn)
        self.table_lp2.Controls.Add(self.cancel_btn)
        self.table_lp1.Controls.Add(self.text_label)
        self.table_lp1.Controls.Add(self.data_gv)
        self.table_lp1.Controls.Add(self.table_lp2)
        self.Controls.Add(self.table_lp1)

    @staticmethod
    def _create_columns(list_of_column_names, data_grid_view):
        for column_name, column_state in list_of_column_names:
            data_gvtbc = DataGridViewTextBoxColumn()
            data_gvtbc.HeaderText = column_name
            data_gvtbc.Name = column_name
            data_gvtbc.ReadOnly = column_state
            data_grid_view.Columns.Add(data_gvtbc)

    def _cancel_action(self, sender, e):
        self.Close()

    def add_row(self, id, _type, name):
        self.data_gv.Rows.Add(id, _type, name)

    def _get_filled_rows(self, sender, e):
        self.filled_rows = []
        current_names = {}

        for row in self.data_gv.Rows:
            organization_type = str(row.Cells[1].Value)
            current_name = str(row.Cells[2].Value).strip()
            current_names[(organization_type, current_name.lower())] = row.Index

        for row in self.data_gv.Rows:
            value = row.Cells[3].Value
            if value is None:
                continue

            new_name = str(value).strip()
            old_name = str(row.Cells[2].Value).strip()
            if not new_name or new_name == old_name:
                continue

            organization_type = str(row.Cells[1].Value)
            name_key = (organization_type, new_name.lower())
            if name_key in current_names and current_names[name_key] != row.Index:
                MessageBox.Show(
                    'The name "{}" is already used by another organization.'.format(new_name),
                    "Invalid name",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Warning,
                )
                return

            if any(
                item[1].lower() == new_name.lower()
                and item[2] == organization_type
                for item in self.filled_rows
            ):
                MessageBox.Show(
                    'The name "{}" is entered more than once.'.format(new_name),
                    "Invalid name",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Warning,
                )
                return

            self.filled_rows.append(
                [row.Cells[0].Value, new_name, organization_type]
            )

        self.is_not_cancel = True
        self.Close()

doc = __revit__.ActiveUIDocument.Document

browser_org_collector = FilteredElementCollector(doc).OfClass(BrowserOrganization)

main_window = MainWindows()
for b_org in browser_org_collector:
    main_window.add_row(b_org.Id, b_org.Type, b_org.Name)
main_window.ShowDialog()

if main_window.is_not_cancel and main_window.filled_rows:
    t = Transaction(doc, "Script : Rename Browser Organization")
    try:
        t.Start()

        for element_id, new_name, _organization_type in main_window.filled_rows:
            doc.GetElement(element_id).Name = new_name

        t.Commit()

        renamed_count = len(main_window.filled_rows)
        organization_word = "organization" if renamed_count == 1 else "organizations"
        MessageBox.Show(
            "Successfully renamed {} browser {}.".format(
                renamed_count,
                organization_word,
            ),
            "Rename Complete",
            MessageBoxButtons.OK,
            MessageBoxIcon.Information,
        )
    except:
        if t.HasStarted():
            t.RollBack()
        raise

