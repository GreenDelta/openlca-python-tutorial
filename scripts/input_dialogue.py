# coding: utf-8
# Tested with openLCA-2.0

from java.lang import Runnable, Double

from org.eclipse.swt.graphics import Point
from org.eclipse.swt.widgets import Display
from org.eclipse.ui.forms import FormDialog
from org.eclipse.ui.forms import IManagedForm
from org.openlca.app.util import UI
from org.eclipse.swt.widgets import Shell


class InputDialog(FormDialog):

    def __init__(self, input):  # type: (dict) -> None
        super(InputDialog, self).__init__(UI.shell())
        self.name = None
        self.amount = None
        self.input = input

    def configureShell(self, new_shell):  # type: (Shell) -> None
        super(InputDialog, self).configureShell(new_shell)
        new_shell.setText("Your title")

    def getInitialSize(self):  # type: () -> Point
        return UI.initialSizeOf(self, 600, 250)

    def createFormContent(self, mform):  # type: (IManagedForm) -> None
        tk = mform.getToolkit()
        body = UI.formBody(mform.getForm(), tk)
        UI.gridLayout(body, 2)
        self.name = UI.formText(body, tk, "Name:")
        self.name.setText(self.input["name"])
        self.amount = UI.formText(body, tk, "Quantity:")
        self.amount.setText(Double.toString(self.input["amount"]))

    def okPressed(self):
        self.input["name"] = self.name.getText()
        self.input["amount"] = Double.parseDouble(self.amount.getText())
        super(InputDialog, self).okPressed()


if __name__ == '__main__':
    input = {"name": "New name", "amount": 0.0}

    class MyRunnable(Runnable):
        def run(self):
            dialog = InputDialog(input)
            dialog.open()

    Display.getDefault().syncExec(MyRunnable())
    print(input)
