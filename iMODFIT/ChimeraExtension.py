# -----------------------------------------------------------------------------
# Class to register the iMODFIT plugin in Chimera.
# The plugin will be located in EM Fitting/Volume Data menu
#
import chimera.extension

# -----------------------------------------------------------------------------
#
class iMODFIT_EMO(chimera.extension.EMO):

    def name(self):
        return 'iMODFIT'
    def description(self):
        return 'Flexible fitting in an exhaustive way through iMODFIT Algorithm'
    def categories(self):
        return ['EM Fitting']
    def icon(self):
        return None
    def activate(self):
        self.module('imodfitgui').show_imodfit_dialog()
        return None

chimera.extension.manager.registerExtension(iMODFIT_EMO(__file__))
