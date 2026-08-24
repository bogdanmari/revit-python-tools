# Create Phase Views

## Description

This Revit script creates an isometric 3D view for every project phase that contains new, demolished, or temporary elements. Each view is named `BIM360 <Phase Name>` and can be configured with a phase filter, two view parameters, and a view template.

By default, the script looks for the following project settings:

- Phase filter: `Current + Demo`
- Category parameter: `Category Name` with the value `Export`
- Subcategory parameter: `Subcategory Name` with the value `BIM360`
- View template: `Export BIM360`

If a matching 3D view already exists, the script updates it instead of creating a duplicate. Phases without relevant elements are skipped. After completion, the script displays the number of created and updated views and a detailed results table.

## How to Use

1. Open the required Revit project.
2. Run `create-phase-views.py` in RevitPythonShell or another compatible Revit Python environment.
3. In the dialog, select the phase filter, category parameter, subcategory parameter, and view template. Select `<None>` for any optional setting that should not be applied.
4. Click **Create / Update** to process the project, or **Cancel** to close the dialog without making changes.
5. Review the summary and results table after the script finishes.

The selected category and subcategory parameters must be text parameters bound to the **Views** category. Any missing or read-only parameters are reported as warnings in the results table.
