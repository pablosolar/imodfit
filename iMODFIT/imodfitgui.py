# ---------------------------------------------------------------------------------
# Dialog to perform flexible fitting through iMODFIT algorithm.
#

import Tkinter
import os
import sys
from subprocess import STDOUT, PIPE, Popen
from sys import platform

import chimera
import iMODFIT
from CGLtk import Hybrid
from Midas import open
from VolumeViewer import Volume
from VolumeViewer import Volume_Menu
from chimera import Molecule
from chimera import dialogs
from chimera import openModels as om, Molecule
from chimera import selection
from chimera.baseDialog import ModelessDialog
from chimera.replyobj import info
from chimera.widgets import ModelOptionMenu


# iMODFIT Class
class iMODFIT_Dialog(ModelessDialog):
    # Title of iMODFIT plugin
    title = 'iMODFIT Flexible Fitting'
    # Name of iMODFIT plugin
    name = 'iMODFIT'
    # Buttons of iMODFIT GUI
    buttons = ('Fit', 'Options', 'Results', 'Close')
    # Path of help guide of iMODFIT plugin
    help = ('imodfit.html', iMODFIT)
    # Name of the folder where iMODFIT plugin is located
    plugin_folder = 'iMODFIT/'
    # Path of the process of iMODFIT
    imodfit = plugin_folder + 'imodfit'
    # Variable to keep the workspace
    cwd = None

    # ---------------------------
    # iMODFIT Chimera Commands

    # iMODFIT in Chimera indicator
    imodfit_chimera_opt = "--chimera"

    # More PDBs
    imodfit_chimera_morepdbs = "--morepdbs"

    # PDB Reference
    imodfit_chimera_pdb_ref = "--pdb_ref"
    imodfit_chimera_pdb_ref_val = None

    # Trajectory (movie)
    imodfit_chimera_t = "-t"

    # Full atom
    imodfit_chimera_F = "-F"

    # Fixing diagonalization
    imodfit_chimera_r = "-r"
    imodfit_chimera_r_val = "0"

    # Rediagonalization
    imodfit_chimera_re = "--rediag"
    imodfit_chimera_re_val = "0"

    # Coarse-grained model
    imodfit_chimera_m = "-m"
    imodfit_chimera_m_val = "2"

    # Modes range
    imodfit_chimera_n = "-n"
    imodfit_chimera_n_val = "0.05"

    # iMODFIT Basename
    imodfit_chimera_o = "-o"

    # Advanced commands
    imodfit_chimera_adv_commands = []


    def fillInUI(self, parent):
        """
        Master function for dialog contents
        :param parent: parent Tkinter frame
        :return:
        """
        t = parent.winfo_toplevel()
        self.toplevel_widget = t
        t.withdraw()

        parent.columnconfigure(0, weight=1)
        row = 0

        ff = Tkinter.Frame(parent)
        ff.grid(row=row, column=0, sticky='w')
        row = row + 1

        # Files selection (only Molecules)
        mlist = [m for m in fit_object_models() if isinstance(m, Molecule)]
        fstart = mlist[0] if mlist else None

        om = ModelOptionMenu(ff, labelpos='w', label_text='Fit ',
                             initialitem=fstart,
                             listFunc=fit_object_models,
                             sortFunc=compare_fit_objects)
        om.grid(row=0, column=0, sticky='w')
        self.object_menu = om

        # Maps selection (only Volumes)
        fm = Volume_Menu(ff, ' in map ')
        fm.frame.grid(row=0, column=1, sticky='w')
        self.map_menu = fm

        hf = Tkinter.Frame(parent)
        hf.grid(row=row, column=0, sticky='w')
        row += 1

        # Resolution
        rs = Hybrid.Entry(hf, 'Resolution ', 5)
        rs.frame.grid(row=0, column=0, sticky='w')
        self.resolution = rs.variable

        # Fix DoF
        fixings = ["None", "50% (fast)", "75% (faster)", "90% (fastest)"]
        self.fixing = apply(Hybrid.Option_Menu, (hf, 'Fix DoF ') + tuple(fixings))
        self.fixing.variable.set("50% (fast)")
        self.fixing.frame.grid(row=0, column=1, sticky='w')

        # Cut-off
        co = Hybrid.Entry(hf, 'Cut-off level ', 5)
        co.frame.grid(row=1, column=0, sticky='w')
        self.cutoff = co.variable

        # Button to get cut-off from the Volume Viewer dialog
        self.save_button = Tkinter.Button(hf, text="Get from Volume Viewer", command=self.get_cutoff)
        self.save_button.grid(row=1, column=1, sticky='w')

        mf = Tkinter.Frame(hf)
        mf.grid(row=2, column=0, sticky='w', columnspan=2)
        mf.columnconfigure(1, weight=1)

        mdf = Tkinter.Frame(mf)
        mdf.grid(row=2, column=0, sticky='w')
        # Model type
        mod = Hybrid.Radiobutton_Row(mdf, 'Atomic Model ', ('Heavy', 'C5', 'CA'), callback=self.full_atoms)
        mod.frame.grid(column=0, sticky='w')
        self.model_type = mod.variable

        # Full atom
        mdf2 = Tkinter.Frame(mf)
        mdf2.grid(row=2, column=1, sticky='w')
        var2 = Tkinter.IntVar()
        self.full_atoms_check = LabeledCheckbutton(mdf2)
        self.full_atoms_check.label.configure(text="Save full")
        self.full_atoms_check.checkbutton.configure(variable=var2, state='disabled')
        self.full_atoms_check.grid(column=1, sticky='w')
        self.full_atoms_v = var2

        # Number of modes
        no = Hybrid.Entry(hf, 'Number of modes ', 5, initial='2')
        no.frame.grid(row=3, column=0, sticky='w')
        self.number_models = no.variable

        # Model percentage
        var = Tkinter.IntVar(value=1)
        c = Tkinter.Checkbutton(hf, text="% Mode", variable=var)
        c.grid(row=3, column=1, sticky='w')
        self.mode_percentage = var

        # Auto-refreshing
        auto = Tkinter.IntVar(value=1)
        c = Tkinter.Checkbutton(hf, text="Auto-refresh model during the iMODFIT process", variable=auto)
        c.grid(row=4, columnspan=2, sticky='w')
        self.auto_refresh = auto

        # Options panel
        rowPanel = row
        op = Hybrid.Popup_Panel(parent)
        opf = op.frame
        opf.grid(row=rowPanel, column=0, sticky='news')
        opf.grid_remove()
        opf.columnconfigure(0, weight=1)
        self.options_panel = op.panel_shown_variable
        row += 1
        orow = 0

        hf = Tkinter.Frame(opf)
        hf.grid(row=0, column=0, sticky='ew')
        hf.columnconfigure(1, weight=1)

        msg = Tkinter.Label(hf, width=40, anchor='w', justify='left')
        msg.grid(row=0, column=0, sticky='ew')
        row = row + 1
        self.message_label = msg

        # Options panel close button
        cb = op.make_close_button(hf)
        cb.grid(row=1, column=1, sticky='e')

        osf = Tkinter.Frame(opf)
        osf.grid(row=2, column=0, sticky='w', columnspan=2)

        # Expert options
        advtext = 'iMODFIT commands for expert users:'
        advh = Tkinter.Label(osf, font="Verdana 10 bold italic", fg="navy", text=advtext)
        advh.grid(row=5, column=0, sticky='w')

        # Commands
        op = Hybrid.Entry(osf, 'Introduce options ', 30)
        op.frame.grid(row=6, column=0, sticky='w')
        self.adv_commands = op.variable

        # Rediags
        rediags = ["None", "0.1", "0.5", "1"]
        self.rediag = apply(Hybrid.Option_Menu, (osf, 'Rediagonalization ') + tuple(rediags))
        self.rediag.variable.set("0.1")
        self.rediag.frame.grid(row=7, column=0, sticky='w')

        # Specify a label width so dialog is not resized for long messages.
        msg = Tkinter.Label(parent, width=40, anchor='w', justify='left')
        msg.grid(row=row, column=0, sticky='ew')
        row = row + 1
        self.message_label = msg

        # Results panel
        row = rowPanel
        re = Hybrid.Popup_Panel(parent)
        ref = re.frame
        ref.grid(row=rowPanel, column=0, sticky='news')
        ref.grid_remove()
        ref.columnconfigure(0, weight=1)
        self.results_panel = re.panel_shown_variable
        row += 1
        orow = 0

        resf = Tkinter.Frame(ref)
        resf.grid(row=0, column=0, sticky='ew')
        resf.columnconfigure(1, weight=1)

        msgR = Tkinter.Label(resf, width=40, anchor='w', justify='left')
        msgR.grid(row=0, column=0, sticky='ew')
        row = row + 1
        self.messageR_label = msgR

        # Results label
        ostextR = 'You can visualize the iMODFIT trajectory here:'
        oshR = Tkinter.Label(resf, font="Verdana 10 bold italic", fg="navy", text=ostextR)
        oshR.grid(row=1, column=0, sticky='w')

        # Results panel close button
        cbR = re.make_close_button(resf)
        cbR.grid(row=1, column=1, sticky='e')

        self.mmf = Tkinter.Frame(ref)
        self.mmf.grid(row=rowPanel, column=0, sticky='w')
        row = row + 1

        # Disable Results panel at first
        self.results_button = self.buttonWidgets['Results']
        self.results_button['state'] = 'disabled'


    def message(self, text):
        """
        Shows a message in iMODFIT Plugin
        :param text: text to show
        :return:
        """
        self.message_label['text'] = text
        self.message_label.update_idletasks()


    def fit_map(self):
        """
        Map chosen to fit into base map.
        :return:
        """
        m = self.object_menu.getvalue()
        if isinstance(m, Volume):
            return m

        return None


    def fit_atoms(self):
        """
        Atoms chosen in dialog for fitting.
        :return:
        """
        m = self.object_menu.getvalue()
        if m == 'selected atoms':
            atoms = selection.currentAtoms()
            return atoms

        if isinstance(m, Molecule):
            return m.atoms

        return []


    def get_options_chimera(self):
        """
        Gets the parameter values introduced by the user
        :return:
        """
        # Model type
        if 'atom' in self.model_type.get():
            self.imodfit_chimera_m_val = "2"
        elif 'C5' in self.model_type.get():
            self.imodfit_chimera_m_val = "1"
        else:
            self.imodfit_chimera_m_val = "0"

        # Number of models
        if len(self.number_models.get()) > 0:
            if self.mode_percentage.get() == 1:
                mode = float(self.number_models.get()) / 100
                if mode >= 0 and mode <= 1:
                    self.imodfit_chimera_n_val = str(mode)
            else:
                self.imodfit_chimera_n_val = str(self.number_models.get())

        # Fix DoF
        if '50' in self.fixing.variable.get():
            self.imodfit_chimera_r_val = "0.5"
        elif '75' in self.fixing.variable.get():
            self.imodfit_chimera_r_val = "0.75"
        elif '90' in self.fixing.variable.get():
            self.imodfit_chimera_r_val = "0.9"

        # Rediagonalization
        if '0.1' in self.rediag.variable.get():
            self.imodfit_chimera_re_val = "0.1"
        elif '0.5' in self.rediag.variable.get():
            self.imodfit_chimera_re_val = "0.5"
        elif '1' in self.rediag.variable.get():
            self.imodfit_chimera_re_val = "0.9"

        # Advanced commands
        if len(self.adv_commands.get()) > 0:
            self.imodfit_chimera_adv_commands = self.adv_commands.get().split()

        # Full Atoms
        if self.full_atoms_v.get() == 1:
            self.imodfit_chimera_adv_commands.append(self.imodfit_chimera_F)


    def Fit(self):
        """
        Performs the iMODFIT process
        :return:
        """
        # If a fitting is performed when Results panel is active, close it
        for widget in self.mmf.winfo_children():
            widget.destroy()
        self.results_panel.set(False)

        # Validation of the parameters introduced by the user
        if self.check_models() is False:
            return

        # Disable Fit, Options and Close buttons when iMODFIT process is performed
        self.disable_process_buttons()

        # Aborting process flag
        self.abort_flag = False

        # Retrieve the full plugin path
        self.plugin_path = __file__[:__file__.index(self.plugin_folder)]

        # -----------------------
        # Calling iMODFIT process
        # -----------------------
        # Get the full path of iMODFIT process by OS
        command = self.plugin_path + self.imodfit

        if platform == "linux" or platform == "linux2":
            command = '_'.join([command, 'linux'])
        elif platform == "darwin":
            command = '_'.join([command, 'mac'])

        # Set the workspace
        self.cwd = self.plugin_path + self.plugin_folder

        # PDB selected in the menu
        pdbSelected = self.object_menu.getvalue()
        self.pdb_basename = (pdbSelected.name).split('.pdb')[0]
        # Map selected in the menu
        mapSelected = self.map_menu.volume()

        # Get options values
        self.get_options_chimera()

        # Retrieve path (absolute or relative)
        map_path = mapSelected.openedAs[0]
        pdb_path = pdbSelected.openedAs[0]
        map_path = os.path.join(os.getcwd(), map_path) if not os.path.isabs(map_path) else map_path
        pdb_path = os.path.join(os.getcwd(), pdb_path) if not os.path.isabs(pdb_path) else pdb_path

        # Retrieve the full command to perform the fitting: imodfit + arguments
        cmd = [command, pdb_path, map_path, self.resolution.get(), self.cutoff.get(),
               self.imodfit_chimera_m, self.imodfit_chimera_m_val,
               self.imodfit_chimera_t,
               self.imodfit_chimera_r, self.imodfit_chimera_r_val,
               self.imodfit_chimera_re, self.imodfit_chimera_re_val,
               self.imodfit_chimera_morepdbs,
               self.imodfit_chimera_n, self.imodfit_chimera_n_val,
               self.imodfit_chimera_o, self.pdb_basename,
               self.imodfit_chimera_opt] + self.imodfit_chimera_adv_commands

        # Execute the command with the respective arguments creating pipes between the process and Chimera
        # Pipes will be associated to the standard output and standard error required to show the process log
        # in the window

        self.imodfit_process = Popen(cmd, stdout=PIPE, stderr=STDOUT, cwd=self.cwd, universal_newlines=True)

        # Text widget for process log that will shows the standard output of the process
        root = Tk()
        root.wm_title("iMODFIT Process Log")
        self.abort_button = Button(root, text="Abort iMODFIT Process")
        self.abort_button.pack(side=BOTTOM, fill=X)
        S = Scrollbar(root)
        T = Text(root, height=30, width=85)
        S.pack(side=RIGHT, fill=Y)
        T.pack(side=LEFT, fill=Y)
        S.config(command=T.yview)
        T.config(yscrollcommand=S.set)
        self.abort_button.configure(command=self.abort)

        # Read first line
        line = self.imodfit_process.stdout.readline()
        # Variables to check the process status and show its output in a friendly format to the user
        iter = False
        model_iter = False
        index_before_last_print = None
        first_ite_sec = True

        # Continue reading the standard output until iMODFIT is finished
        # If the current line is an iteration for a model, replace in the widget the last showed
        # If it is a new model or is part of the iMODFIT process, inserts the line at the end of the widget
        while line:
            if len(line.strip()) == 0:
                line = self.imodfit_process.stdout.readline()
                continue
            if iter is False or (iter is True and 'NMA' in line):
                T.insert(END, line)
                model_iter = True
            elif iter is True and ' s' in line:
                if first_ite_sec is True:
                    T.insert(END, line)
                    model_iter = True
                else:
                    T.delete(index_before_last_print + "-1c linestart", index_before_last_print)
                    T.insert(END, line)
                    first_ite_sec = False
            elif model_iter is True:
                index_before_last_print = T.index(END)
                T.insert(END, line)
                model_iter = False
            elif iter is True and ' s' not in line:
                T.delete(index_before_last_print + "-1c linestart", index_before_last_print)
                T.insert(END, line)
            T.update()
            T.yview(END)
            line = self.imodfit_process.stdout.readline()
            if 'new_frame' in line:
                line = line.replace('new_frame', '')
                if self.auto_refresh.get() == 1:
                    self.refresh_model()
            if ('NMA_time' in line and 'Score' in line):
                iter = True
            if ' s' in line and iter is True:
                first_ite_sec = True
                model_iter = True
                if index_before_last_print is not None:
                    T.delete(index_before_last_print + "-1c linestart", index_before_last_print)
                index_before_last_print = T.index(END)
            if 'Convergence' in line:
                iter = False
            if 'Range of used modes' in line:
                self.load_model()
            if 'Error' in line:
                self.abort_flag = True

        # When iMODFIT process is finished, the results are set into the Results panel...
        self.refresh_model()
        self.fill_results()
        # and the plugin buttons are enabled again
        self.enable_process_buttons()

        if not self.abort_flag:
            T.insert(END, "\n\n --> iMODFIT Process has finished. Check 'Results' button to visualize solution. <--\n")
            T.update()
            T.yview(END)
            self.Results()
        else:
            T.insert(END, "\n\n --> iMODFIT Process has been aborted. <--\n")
            T.update()
            T.yview(END)
            self.abort_flag = False


    def fill_results(self):
        """
        Fills the Results panel with the corresponding components
        :return:
        """
        # Button to open the MD Movie created by iMODTFIT with the model trajectories
        self.open_md_movie = Tkinter.Button(self.mmf, text="Open movie", command=self.open_movie)
        self.open_md_movie.grid(row=1, column=0, sticky='w')
        # Name of the trajectory movie
        self.imovie = ''.join([plugin_folder, '_'.join([self.pdb_basename, 'movie.pdb'])])


    def load_model(self):
        """
        Loads actual model selected
        :return:
        """
        model_path = os.path.join(self.cwd, '_'.join([self.pdb_basename, 'fitted.pdb']))
        if os.path.exists(model_path):
            open(model_path, filetype="pdb")


    def refresh_model(self):
        """
        Refresh actual model selected
        :return:
        """
        self.show_fitted_molecule(True)


    def show_fitted_molecule(self, fitted):
        """
        Reads the coordinates of the fitted molecule and updates the original
        molecule position to show the fitting made by iMODFIT
        :param fitted: flag to choose the original molecule or the fitted one
        :return:
        """
        try:
            # Get opened molecule (the one selected in the menu)
            p = self.object_menu.getvalue()
            mlist = [m for m in fit_object_models() if isinstance(m, Molecule)]
            for mol in mlist:
                if self.pdb_basename in mol.name:
                    p = mol

            # Get some atom
            a0 = p.atoms[0]
            # Coordinates array
            cs = []
            # Names array
            ns = []

            # Depends on the button state, choose the original molecule
            # or the fitted one to update the position
            fitted_mol = None
            if fitted is True:
                fitted_mol = ''.join([self.cwd, '_'.join([self.pdb_basename, 'fitted.pdb'])])
            else:
                # fitted_mol = self.object_menu.getvalue().openedAs[0]
                fitted_mol = ''.join([self.cwd, 'imodfit_model.pdb'])

            # Read the coordinates of the fitted molecule and fill
            # coordinates and names arrays
            with open(fitted_mol) as pdbfile:
                for line in pdbfile:
                    if line[:4] == 'ATOM' or line[:6] == "HETATM":
                        # Split the line according to PDB format
                        n = line[12:16]
                        # Construct a copy of coordinates
                        c = a0.coord()
                        c[0] = x = float(line[30:38])
                        c[1] = y = float(line[38:46])
                        c[2] = z = float(line[46:54])
                        # Store all atomic coordinates
                        cs.append(c)
                        # store names (for self-consistency checking)
                        ns.append(n.strip())

            # MON: Set continue if not all atoms were successfully read

            # Update coordinates of the molecule
            # coordinate array index
            i = 0
            for a in p.atoms:
                # Check if both atoms are the same
                # if atom names don't match
                if a.name != ns[i]:
                    print 'Warning! ', ns[i], ' and ', a.name, ' mismatch at residue ', a.residue
                    print 'Searching ', ns[i], ' in residue ', a.residue
                    isfound = False
                    for b in a.residue.atoms:
                        # Atom found
                        if b.name == ns[i]:
                            print 'Atom (', ns[i], ') found. Updating (', b.name, ') coordinates'
                            # Set new coordinates into "b" atom
                            b.setCoord(cs[i])
                            isfound = True
                            break
                    if not isfound:
                        print 'Error! Atom ', ns[i], ' not found in residue ', a.residue
                # if atom names match
                else:
                    # Set new coordinates into "a" atom
                    a.setCoord(cs[i])

                # Update index
                i = i + 1
        except:
            pass


    def open_movie(self):
        """
        Opens the MD movie created by iMODTFIT with the model trajectories
        :return:
        """
        # Import the native dialog MovieDialog from Chimera
        from Movie.gui import MovieDialog
        # import the loadEnsemble native functionality from Chimera to load the movie
        from Trajectory.formats.Pdb import loadEnsemble


        # Load the movie created by iMODFIT
        movie = ''.join([self.plugin_path, self.imovie])
        info('\n')
        info(movie)
        info('\n')
        loadEnsemble(("single", movie), None, None, MovieDialog)


    def disable_process_buttons(self):
        """
        Disables the the iMODFIT GUI Fit, Options, Close and Results buttons
        :return:
        """
        self.fit_button = self.buttonWidgets['Fit']
        self.fit_button['state'] = 'disabled'
        self.options_button = self.buttonWidgets['Options']
        self.options_button['state'] = 'disabled'
        self.close_ch_button = self.buttonWidgets['Close']
        self.close_ch_button['state'] = 'disabled'
        self.results_button['state'] = 'disabled'


    def enable_process_buttons(self):
        """
        Enables the the iMODFIT GUI Fit, Options, Close and Results buttons
        :return:
        """
        self.fit_button = self.buttonWidgets['Fit']
        self.fit_button['state'] = 'normal'
        self.options_button = self.buttonWidgets['Options']
        self.options_button['state'] = 'normal'
        self.close_ch_button = self.buttonWidgets['Close']
        self.close_ch_button['state'] = 'normal'
        if not self.abort_flag:
            self.results_button['state'] = 'normal'


    def Options(self):
        """
        When Options button is pressed, the Result panel is hidden and Options panel is shown
        :return:
        """
        self.results_panel.set(False)
        self.options_panel.set(not self.options_panel.get())


    def Results(self):
        """
        When Results button is pressed, the Options panel is hidden and Results panel is shown
        :return:
        """
        self.options_panel.set(False)
        self.results_panel.set(not self.results_panel.get())
        self.imodfit_chimera_adv_commands = []


    def abort(self):
        """
        Aborts iMODFIT Process
        :return:
        """
        self.imodfit_process.kill()
        self.enable_process_buttons()


    def get_cutoff(self):
        """
        Gets the cut-off level value from the Volume Viewer dialog

        Useful when the user does not know an appropiate resolution and plays
        with the map density in this dialog.
        :return:
        """
        # validate if the map is loaded/choosed
        bmap = self.map_menu.data_region()
        if bmap is None:
            self.message('Choose map.')
            return

        vdlg = dialogs.find("volume viewer")

        # Get the cut-off level from the Volume Viewer dialog
        cutoff_panel = vdlg.thresholds_panel.threshold.get()

        # Set the cut-off value in iMODFIT with the previous value
        self.cutoff.set(cutoff_panel)
        self.message("")


    def check_models(self):
        """
        Validates the values of the parameteres introduced by the users.

        Moreover, check if molecule and maps are loaded
        :return:
        """
        fatoms = self.fit_atoms()
        fmap = self.fit_map()
        bmap = self.map_menu.data_region()
        if (len(fatoms) == 0 and fmap is None) or bmap is None:
            self.message('Choose model and map.')
            return False
        if fmap == bmap:
            self.message('Chosen maps are the same.')
            return False
        if len(self.cutoff.get()) == 0:
            self.message('Cutoff must be defined.')
            return False
        if len(self.resolution.get()) == 0:
            self.message('Resolution must be defined.')
            return False
        if float(self.resolution.get()) < 0 or float(self.resolution.get()) >= 60:
            self.message('Resolution must be less than 100.')
            return False
        self.message("")
        return True


    def full_atoms(self):
        """
        Enables/Disables the full-atoms model check button
        :return:
        """
        # Model type
        if 'Heavy' in self.model_type.get():
            self.full_atoms_check.checkbutton.configure(state='disabled')
            self.full_atoms_v.set(0)
        else:
            self.full_atoms_check.checkbutton.configure(state='normal')


    def representsInt(self, number):
        """
        Validates if a string represents an integer
        :param number: a string representing a number
        :return:
        """
        try:
            int(number)
            return True
        except ValueError:
            return False


    def representsFloat(self, number):
        """
        Validates if a string represents an integer
        :param number: a string representing a number
        :return:
        """
        try:
            float(number)
            return True
        except ValueError:
            return False


# Custom inner class for a right-sided labeled checkbutton
class LabeledCheckbutton(Tkinter.Frame):


    def __init__(self, root):
        """
        Constructor
        :param root: Tkinter frame to allocate widgets
        """
        Tkinter.Frame.__init__(self, root)
        self.checkbutton = Tkinter.Checkbutton(self)
        self.label = Tkinter.Label(self)
        self.label.grid(row=0, column=0, padx=(10, 0))
        self.checkbutton.grid(row=0, column=1)


def fit_object_models():
    """
    Returns a list of molecules from the models opened in Chimera
    to be selectables for the fitting
    :return:
    """
    mlist = om.list(modelTypes=[Molecule])
    folist = ['selected atoms'] + mlist
    return folist


def compare_fit_objects(a, b):
    """
    Puts 'selected atoms'pyt first, then all molecules, then all volumes.
    :param a: atom A
    :param b: atom B
    :return: true or false depending on the comparison
    """
    if a == 'selected atoms':
        return -1
    if b == 'selected atoms':
        return 1
    from VolumeViewer import Volume
    from chimera import Molecule


    if isinstance(a, Molecule) and isinstance(b, Volume):
        return -1
    if isinstance(a, Volume) and isinstance(b, Molecule):
        return 1
    return cmp((a.id, a.subid), (b.id, b.subid))


def show_imodfit_dialog():
    """
    Shows the iMODFIT Dialog in Chimera when it is registered
    :return:
    """
    return dialogs.display(iMODFIT_Dialog.name)


# Registers the iMODFIT Dialog in Chimera
dialogs.register(iMODFIT_Dialog.name, iMODFIT_Dialog, replace=True)
