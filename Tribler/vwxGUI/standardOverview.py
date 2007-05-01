import wx, os, sys, os.path
import wx.xrc as xrc
from Tribler.vwxGUI.GuiUtility import GUIUtility
from safeguiupdate import FlaglessDelayedInvocation
from traceback import print_exc

OVERVIEW_MODES = ['filesMode', 'personsMode', 'profileMode', 'friendsMode', 'subscriptionsMode', 'messageMode', 'libraryMode']
DEBUG = True

class standardOverview(wx.Panel,FlaglessDelayedInvocation):
    """
    Panel that shows one of the overview panels
    """
    def __init__(self, *args):
        if len(args) == 0:
            pre = wx.PrePanel()
            # the Create step is done by XRC.
            self.PostCreate(pre)
            self.Bind(wx.EVT_WINDOW_CREATE, self.OnCreate)
        else:
            wx.Panel.__init__(self, *args)
            self._PostInit()
        
    def OnCreate(self, event):
        self.Unbind(wx.EVT_WINDOW_CREATE)
        wx.CallAfter(self._PostInit)
        event.Skip()
        return True
    
    def _PostInit(self):
        # Do all init here
        FlaglessDelayedInvocation.__init__(self)
        self.guiUtility = GUIUtility.getInstance()
        self.mode = None
        self.filter1 = None
        self.filter2 = None
        self.data = {} #keeps gui elements for each mode
        for mode in OVERVIEW_MODES:
            self.data[mode] = {} #each mode has a dictionary of gui elements with name and reference
        self.currentPanel = None
        self.addComponents()
        #self.Refresh()
        self.guiUtility.initStandardOverview(self)
        
    def addComponents(self):
        self.hSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.hSizer)
        self.SetAutoLayout(1)
        self.Layout()
        
    def setMode(self, mode, filter1, filter2, datalist):
        
        if self.mode != mode: 
            self.mode = mode
            self.filter1 = filter1
            self.data[self.mode]['data'] = datalist               
            self.refreshMode()
        elif self.mode == mode and self.filter1 != filter1:        
            self.mode = mode            
            self.filter1 = filter1                           
            self.data[self.mode]['data'] = datalist
            self.setData()                   
        elif self.mode == mode and self.filter2 != filter2:
            self.mode = mode            
            self.filter2 = filter2
            self.data[self.mode]['data'] = datalist
            self.setData()   
            
            
    def refreshMode(self):
        # load xrc
        self.oldpanel = self.currentPanel
        #self.Show(False)
        
        self.currentPanel = self.loadPanel()
        assert self.currentPanel, "Panel could not be loaded"
        self.setData()
        #self.currentPanel.GetSizer().Layout()
        #self.currentPanel.Enable(True)
        self.currentPanel.Show(True)
        
        if self.oldpanel:
            self.hSizer.Detach(self.oldpanel)
            self.oldpanel.Hide()
            #self.oldpanel.Disable()
        
        self.hSizer.Add(self.currentPanel, 1, wx.ALL|wx.EXPAND, 0)
        
        self.hSizer.Layout()
        wx.CallAfter(self.hSizer.Layout)
        wx.CallAfter(self.currentPanel.Refresh)
        #self.Show(True)
        
        
    def loadPanel(self):
        currentPanel = self.data[self.mode].get('panel',None)
        modeString = self.mode[:-4]
        print 'modeString='+modeString
        if not currentPanel:
            xrcResource = os.path.join('Tribler','vwxGUI', modeString+'Overview.xrc')
            panelName = modeString+'Overview'
            try:
                currentPanel = grid = pager = None
                res = xrc.XmlResource(xrcResource)
                # create panel
                currentPanel = res.LoadPanel(self, panelName)
                grid = xrc.XRCCTRL(currentPanel, modeString+'Grid')
                pager = xrc.XRCCTRL(currentPanel, 'standardPager')
                if not currentPanel:
                    #load dummy panel
                    dummyFile = os.path.join('Tribler','vwxGUI', 'dummyOverview.xrc')
                    dummy_res = xrc.XmlResource(dummyFile)
                    currentPanel = dummy_res.LoadPanel(self, 'dummyOverview')
                    grid = xrc.XRCCTRL(currentPanel, 'dummyGrid')
                    pager = xrc.XRCCTRL(currentPanel, 'standardPager')
                if not currentPanel: # or not grid or not pager:
                    raise Exception('standardOverview: Could not find panel, grid or pager')
                
                # Save paneldata in self.data
                self.data[self.mode]['panel'] = currentPanel
                self.data[self.mode]['grid'] = grid
                self.data[self.mode]['pager'] = pager
                pager.setGrid(grid)
            except:
                print 'Error: Could not load panel, grid and pager for mode %s' % self.mode
                print 'Tried panel: %s=%s, grid: %s=%s, pager: %s=%s' % (panelName, currentPanel, modeString+'Grid', grid, 'standardPager', pager)
                print_exc()
        return currentPanel
     
    def setData(self):        
        grid = self.data[self.mode].get('grid')
        if grid:
            grid.setData(self.data[self.mode].get('data'))
        
    def updateSelection(self):
        grid = self.data[self.mode].get('grid')
        if grid:
            grid.updateSelection()
        
        
    def getFirstItem(self):
        data = self.data[self.mode]['data']
        if len(data) > 0:
            return data[0]
        else:
            print 'standardOverview: Error, could not return firstItem, data=%s' % data
            return None
        
    def refreshTorrentStats_network_callback(self):
        """ Called by network thread """
        self.invokeLater(self.refreshTorrentStats)
        
    def refreshTorrentStats(self):
        if self.mode == 'libraryMode':
            grid = self.data[self.mode].get('grid')
            grid.refreshData()
