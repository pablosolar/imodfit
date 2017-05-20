# ---------------------------------------------------------------------------------
# Dialog to perform flexible fitting through iMODFIT algorithm.
#

import chimera
from chimera.baseDialog import ModelessDialog
import iMODFIT

# ---------------------------------------------------------------------------------
# iMODFIT Plugin Dialog
#
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
  # Name of the fitted pdb generated after iMODFIT process
  fitted_molecule = "imodfit_fitted.pdb"
  # Name of the trajectory movie
  imovie = plugin_folder + "imodfit_movie.pdb"

  #---------------------------
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

  # Advanced commands
  imodfit_chimera_adv_commands = []

  #-------------------------------------------------
  # Master function for dialog contents
  #
  def fillInUI(self, parent):

    t = parent.winfo_toplevel()
    self.toplevel_widget = t
    t.withdraw()

    parent.columnconfigure(0, weight = 1)
    row = 0

    import Tkinter
    from CGLtk import Hybrid
    from VolumeViewer import Volume_Menu

    ff = Tkinter.Frame(parent)
    ff.grid(row = row, column = 0, sticky = 'w')
    row = row + 1

    # Files selection (only Molecules)
    from chimera import Molecule
    mlist = [m for m in fit_object_models() if isinstance(m, Molecule)]
    fstart = mlist[0] if mlist else None
    from chimera.widgets import ModelOptionMenu
    om = ModelOptionMenu(ff, labelpos = 'w', label_text = 'Fit ',
                         initialitem = fstart,
                         listFunc = fit_object_models,
                         sortFunc = compare_fit_objects)
    om.grid(row = 0, column = 0, sticky = 'w')
    self.object_menu = om

    # Maps selection (only Volumes)
    fm = Volume_Menu(ff, ' in map ')
    fm.frame.grid(row = 0, column = 1, sticky = 'w')
    self.map_menu = fm

    hf = Tkinter.Frame(parent)
    hf.grid(row=row, column=0, sticky='w')
    row += 1

    # Resolution
    rs = Hybrid.Entry(hf, 'Resolution ', 5)
    rs.frame.grid(row=0, column=0, sticky='w')
    self.resolution = rs.variable

    # Fix DoF
    from CGLtk import Hybrid
    fixings = ["None", "50% (fast)", "75% (faster)", "90% (fastest)"]
    self.fixing = apply(Hybrid.Option_Menu, (hf, 'Fix DoF ')  + tuple(fixings))
    self.fixing.variable.set("50% (fast)")
    self.fixing.frame.grid(row=0, column=1, sticky='w')

    # Cut-off
    co = Hybrid.Entry(hf, 'Cut-off level ', 5)
    co.frame.grid(row=1, column=0, sticky='w')
    self.cutoff = co.variable

    # Button to get cut-off from the Volume Viewer dialog
    self.save_button = Tkinter.Button(hf, text="Get from Volume Viewer", command=self.get_cutoff)
    self.save_button.grid(row=1, column=1, sticky='w')

    # Model type
    mod = Hybrid.Radiobutton_Row(hf, 'Model ', ('Heavy-atoms', 'C5', 'CA'))
    mod.frame.grid(columnspan=2, sticky='w')
    self.model_type = mod.variable

    # Number of models
    no = Hybrid.Entry(hf, 'Number of modes ', 5)
    no.frame.grid(row=3, column=0, sticky='w')
    self.number_models = no.variable

    # Model percentage
    var = Tkinter.IntVar()
    c = Tkinter.Checkbutton(hf, text="% Mode", variable=var)
    c.grid(row=3, column=1, sticky='w')
    self.mode_percentage = var

    # Options panel
    rowPanel = row
    op = Hybrid.Popup_Panel(parent)
    opf = op.frame
    opf.grid(row = rowPanel, column = 0, sticky = 'news')
    opf.grid_remove()
    opf.columnconfigure(0, weight=1)
    self.options_panel = op.panel_shown_variable
    row += 1
    orow = 0

    hf = Tkinter.Frame(opf)
    hf.grid(row=0, column=0, sticky='ew')
    hf.columnconfigure(1, weight=1)

    msg = Tkinter.Label(hf, width = 40, anchor = 'w', justify = 'left')
    msg.grid(row=0, column = 0, sticky = 'ew')
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
    self.rediag = apply(Hybrid.Option_Menu, (osf, 'Rediagonalization ')  + tuple(rediags))
    self.rediag.variable.set("0.1")
    self.rediag.frame.grid(row=7, column=0, sticky='w')


    # Specify a label width so dialog is not resized for long messages.
    msg = Tkinter.Label(parent, width = 40, anchor = 'w', justify = 'left')
    msg.grid(row = row, column = 0, sticky = 'ew')
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
    ostextR = 'Click button to switch between original and fitted model'
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

  # ---------------------------------------------------------------------------
  # Shows a message in iMODFIT Plugin
  #
  def message(self, text):

    self.message_label['text'] = text
    self.message_label.update_idletasks()

  # ---------------------------------------------------------------------------
  # Map chosen to fit into base map.
  #
  def fit_map(self):

    m = self.object_menu.getvalue()
    from VolumeViewer import Volume
    if isinstance(m, Volume):
      return m
    
    return None

  # ---------------------------------------------------------------------------
  # Atoms chosen in dialog for fitting.
  #
  def fit_atoms(self):

    m = self.object_menu.getvalue()
    if m == 'selected atoms':
      from chimera import selection
      atoms = selection.currentAtoms()
      return atoms

    from chimera import Molecule
    if isinstance(m, Molecule):
      return m.atoms
    
    return []

  # ---------------------------------------------------------------------------
  # Gets the parameter values introduced by the user
  #
  def get_options_chimera (self):

    # Model type
    if 'atom' in self.model_type.get():
      self.imodfit_chimera_m_val = "2"
    elif '3BB2R' in self.model_type.get():
      self.imodfit_chimera_m_val = "1"
    else:
      self.imodfit_chimera_m_val = "0"

    # Number of models
    if len(self.number_models.get()) > 0:
      if self.mode_percentage.get()  == 1:
        mode = float(self.number_models.get())/100
        if mode >= 0 and mode <=1:
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

  # ---------------------------------------------------------------------------
  # Performs the iMODFIT process
  #
  def Fit(self):

    # If a fitting is performed when Results panel is active, close it
    for widget in self.mmf.winfo_children():
      widget.destroy()
    self.results_panel.set(False)

    # Validation of the parameters introduced by the user
    if self.check_models() is False:
      return

    # Disable Fit, Options and Close buttons when iMODFIT process is performed
    self.disable_process_buttons()

    # Retrieve the full plugin path
    self.plugin_path = __file__[:__file__.index(self.plugin_folder)]

    #-----------------------
    # Calling iMODFIT process
    #-----------------------
    from subprocess import STDOUT, PIPE, Popen
    import os, sys

    # Get the full path of iMODFIT process
    command = self.plugin_path + self.imodfit
    # Set the workspace
    self.cwd = self.plugin_path + self.plugin_folder

    # PDB selected in the menu
    pdbSelected = self.object_menu.getvalue()
    # Map selected in the menu
    mapSelected = self.map_menu.volume()

    # Get options values
    self.get_options_chimera()

    # Retrieve the full command to perform the fitting: imodfit + arguments
    cmd = [command, pdbSelected.openedAs[0], mapSelected.openedAs[0], self.resolution.get(), self.cutoff.get(),
           self.imodfit_chimera_m, self.imodfit_chimera_m_val,
           self.imodfit_chimera_t,
           self.imodfit_chimera_r, self.imodfit_chimera_r_val,
           self.imodfit_chimera_re, self.imodfit_chimera_re_val,
           self.imodfit_chimera_morepdbs,
           self.imodfit_chimera_n, self.imodfit_chimera_n_val] + self.imodfit_chimera_adv_commands

    # Execute the command with the respective arguments creating pipes between the process and Chimera
    # Pipes will be associated to the standard output and standard error required to show the process log
    # in the window
    imodfit_process = Popen(cmd, stdout=PIPE, stderr=PIPE, cwd=self.cwd, universal_newlines=True)

    # Text widget for process log that will showthe standard output of the process
    from Tkinter import *
    root = Tk()
    root.wm_title("iMODFIT Process Log")
    S = Scrollbar(root)
    T = Text(root, height=30, width=85)
    S.pack(side=RIGHT, fill=Y)
    T.pack(side=LEFT, fill=Y)
    S.config(command=T.yview)
    T.config(yscrollcommand=S.set)

    # Read first line
    line = imodfit_process.stdout.readline()
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
          line = imodfit_process.stdout.readline()
          continue
        if iter is False or (iter is True and 'NMA' in line):
          T.insert(END, line)
          model_iter = True
        elif iter is True and 'sec' in line:
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
        elif iter is True and 'sec' not in line:
          T.delete(index_before_last_print + "-1c linestart", index_before_last_print)
          T.insert(END, line)
        T.update()
        T.yview(END)
        line = imodfit_process.stdout.readline()
        if ('NMA_time' in line and 'Score' in line):
          iter = True
        if 'sec' in line and iter is True:
          first_ite_sec = True
          model_iter = True
          if index_before_last_print is not None:
            T.delete(index_before_last_print + "-1c linestart", index_before_last_print)
          index_before_last_print = T.index(END)
        if 'Convergence' in line:
          iter = False

    T.insert(END, "\n\n --> iMODFIT Process has finished. Check 'Results' button to visualize solution. <--\n")
    T.update()
    T.yview(END)

    # When iMODFIT process is finished, the results are set into the Results panel...
    self.fill_results()
    # and the plugin buttons are enabled again
    self.enable_process_buttons()

  # ---------------------------------------------------------------------------
  # Fill the Results panel with the corresponding components
  #
  def fill_results(self):

    # Button to switch between the original molecule and the fitted one with iMODFIT
    import Tkinter
    self.save_button =  Tkinter.Button (self.mmf, text="Show fitted molecule", command=self.switch_original_fitted)
    self.save_button.grid(row=0, column=0, sticky='w')

    # Button to copy to the Model Panel the fitted molecule
    self.save_fitted = Tkinter.Button(self.mmf, text="Copy fitted molecule", command=self.save_fitted_molecule)
    self.save_fitted.grid(row=0, column=1, sticky='w')
    self.save_fitted['state'] = 'disabled'

    # Button to open the MD Movie created by iMODTFIT with the model trajectories
    self.open_md_movie = Tkinter.Button(self.mmf, text="Open movie", command=self.open_movie)
    self.open_md_movie.grid(row=1, column=0, sticky='w')

  # ---------------------------------------------------------------------------
  # Switchs between the original molecule and the fitted one with iMODFIT
  #
  def switch_original_fitted(self):

    if self.save_button["text"] == "Show fitted molecule":
      # Show fitted molecule
      self.show_fitted_molecule(True)
      self.save_button["text"] = "Show original molecule"
      self.save_fitted['state'] = 'normal'
    else:
      # Show original molecule
      self.show_fitted_molecule(False)
      self.save_button["text"] = "Show fitted molecule"
      self.save_fitted['state'] = 'disabled'

  # ---------------------------------------------------------------------------
  # Reads the coordinates of the fitted molecule and updates the original
  # molecule position to show the fitting made by iMODFIT
  #
  def show_fitted_molecule(self, fitted):

    # Get opened molecule (the one selected in the menu)
    p = self.object_menu.getvalue()
    # Get some atom
    a0 = p.atoms[0]
    # Coordinates array
    cs = []
    # Names array
    ns = []

    # Depends on the button state, chose the original molecule
    # or the fitted one to update the position
    fitted_mol = None
    if fitted is True:
      fitted_mol = self.cwd + self.fitted_molecule
    else:
      fitted_mol = self.object_menu.getvalue().openedAs[0]

    # Read thhe coordinates of the fitted molecule and fill
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

  # ---------------------------------------------------------------------------
  # Makes a copy to the Model Panel of the fitted molecule
  #
  def save_fitted_molecule(self):

    # Get opened molecule (the one selected in the menu)
    m = self.object_menu.getvalue()

    # Make copy using the copy_molecule native functionality from Chimera
    from Molecule import copy_molecule
    mc = copy_molecule(m)

    # Set copy name
    mc.name = m.name.split('.')[0] + '_imodfit.pdb'

    # Add copy to list of open models
    chimera.openModels.add([mc])

  # ---------------------------------------------------------------------------
  # Opens the MD movie created by iMODTFIT with the model trajectories
  #
  def open_movie(self):

    # Import the native dialog MovieDialog from Chimera
    from Movie.gui import MovieDialog
    # import the loadEnsemble native functionality from Chimera to load the movie
    from Trajectory.formats.Pdb import loadEnsemble

    # Load the movie created by iMODFIT
    movie = self.plugin_path + self.imovie
    loadEnsemble(("single", movie), None, None, MovieDialog)

  # ---------------------------------------------------------------------------
  # Disables the the iMODFIT GUI Fit, Options, Close and Results buttons
  #
  def disable_process_buttons(self):

    self.fit_button = self.buttonWidgets['Fit']
    self.fit_button['state'] = 'disabled'
    self.options_button = self.buttonWidgets['Options']
    self.options_button['state'] = 'disabled'
    self.close_ch_button = self.buttonWidgets['Close']
    self.close_ch_button['state'] = 'disabled'
    self.results_button['state'] = 'disabled'

  # ---------------------------------------------------------------------------
  # Enables the the iMODFIT GUI Fit, Options, Close and Results buttons
  #
  def enable_process_buttons(self):

    self.fit_button = self.buttonWidgets['Fit']
    self.fit_button['state'] = 'normal'
    self.options_button = self.buttonWidgets['Options']
    self.options_button['state'] = 'normal'
    self.close_ch_button = self.buttonWidgets['Close']
    self.close_ch_button['state'] = 'normal'
    self.results_button['state'] = 'normal'

  # ---------------------------------------------------------------------------
  # When Options button is pressed, the Result panel is hidden and Options
  # panel is shown
  #
  def Options(self):

    self.results_panel.set(False)
    self.options_panel.set(not self.options_panel.get())

  # ---------------------------------------------------------------------------
  # When Results button is pressed, the Options panel is hidden and Results
  # panel is shown
  #
  def Results(self):

    self.options_panel.set(False)
    self.results_panel.set(not self.results_panel.get())

  # -----------------------------------------------------------------------------
  # Gets the cut-off level value from the Volume Viewer dialog
  # Useful when the user does not know an appropiate resolution and plays
  # with the map density in this dialog.
  #
  def get_cutoff (self):

    # validate if the map is loaded/choosed
    bmap = self.map_menu.data_region()
    if bmap is None:
      self.message('Choose map.')
      return

    # Import the native dialog Volume Viewer from Chimera
    from chimera import dialogs
    vdlg = dialogs.find("volume viewer")

    # Get the cut-off level from the Volume Viewer dialog
    cutoff_panel = vdlg.thresholds_panel.threshold.get()

    # Set the cut-off value in iMODFIT with the previous value
    self.cutoff.set(cutoff_panel)
    self.message("")

  # -----------------------------------------------------------------------------
  # Validates the values of the parameteres introduced by the users.
  # Moreover, check if molecule and maps are loaded
  #
  def check_models (self):

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

  #----------------------------------------------
  # Validates if a string represents an integer
  #
  def representsInt(self, number):

    try:
      int(number)
      return True
    except ValueError:
      return False

  # ----------------------------------------------
  # Validates if a string represents an integer
  #
  def representsFloat(self, number):

    try:
      float(number)
      return True
    except ValueError:
      return False

# -----------------------------------------------------------------------------
# Returns a list of molecules from the models opened in Chimera
# to be selectables for the fitting
#
def fit_object_models():

  from chimera import openModels as om, Molecule
  mlist = om.list(modelTypes = [Molecule])
  folist = ['selected atoms'] + mlist
  return folist

# -----------------------------------------------------------------------------
# Puts 'selected atoms' first, then all molecules, then all volumes.
#
def compare_fit_objects(a, b):

  if a == 'selected atoms':
    return -1
  if b == 'selected atoms':
    return 1
  from VolumeViewer import Volume
  from chimera import Molecule
  if isinstance(a,Molecule) and isinstance(b,Volume):
    return -1
  if isinstance(a,Volume) and isinstance(b,Molecule):
    return 1
  return cmp((a.id, a.subid), (b.id, b.subid))

# -----------------------------------------------------------------------------
# Shows the iMODFIT Dialog in Chimera when it is registered
#
def show_imodfit_dialog():

  from chimera import dialogs
  return dialogs.display(iMODFIT_Dialog.name)

# -----------------------------------------------------------------------------
# Registers the iMODFIT Dialog in Chimera
#
from chimera import dialogs
dialogs.register(iMODFIT_Dialog.name, iMODFIT_Dialog, replace = True)
