import os, string, numpy, scipy.stats, re, pylab, matplotlib, pylab
import matplotlib.pyplot as plt
from matplotlib import rcParams

DefaultBaseDirectory='/home/jack/Documents/School/Grad/Adhesive Test/'
ipackdir='/home/jack/Documents/School/Grad/Adhesive Test/Interpack 2009/Final Draft'

class BoardList(dict):
    """List for storing Board objects"""
    def types(self):
        temp_list=[]
        for board in self.values():
            temp_list.append(board.type)
        return list(set(temp_list))

    def bytype(self,type='All'):
        Types=self.types()
        temp_list=[]
        for i in range(len(Types)):
            temp_list.append([])
            for board in self.values():
                if board.type == Types[i]:
                    temp_list[i].append(board)
            temp_list[i].sort()
        if type == 'All':
            return sorted(temp_list)
        return sorted(temp_list[Types.index(type)])

    def all(self):
        return sorted(self.values())
    

class Board():
    """board object: has attributes of .cycles, .name, and .type"""
    def __init__(self, type, name):
        self.type=type
        self.name=name
        self.cycles=CycleList()
        
    def __str__(self): return self.name

    def __repr__(self): return '<'+self.name+'>'
    
    def __cmp__(self,other):
        if self.type != other.type:
            return cmp(self.type,other.type)
        if ('THER' in self.name and 'THER' in other.name) or ('PSAC' in self.name and 'PSAC' in other.name):
            return cmp(int(re.search('(\d+)',self.name).group(1)),\
                int(re.search('(\d+)',other.name).group(1)))
        if '-' in self.name and '-' in other.name:
            return cmp(int(re.search('-(\d+)',self.name).group(1)),\
                int(re.search('-(\d+)',other.name).group(1)))


class CycleList(list):
    """list of cycles: is an attribute of a board object as .cycles:
    has attributes .clamped(), .unclamped(), .numbers, and .units"""
    def __init__(self):
        self=[]

    def __str__(self):
        l=''
        for cycle in sorted(self):
            l+=cycle.name+'\n'
        return l 

    def __repr__(self):
        l=[]
        for cycle in sorted(self):
            l.append(cycle.name)
        return ', '.join(l)

    def numbers(self):
        l=[]
        for cycle in sorted(self):
            l.append(int(re.search('(\d+)(.+)',cycle.name).group(1)))
        return l    

    def units(self):
        return re.search('(\d+)(.+)',self[0].name).group(2).replace(' ','')
        
    def clamped(self):
        return [cycle for cycle in self if ' U' not in cycle.name]
    
    def unclamped(self):
        return [cycle for cycle in self if ' U' in cycle.name]


class Cycle():
    """cycle object: is a part of a CycleList() list:
    has attributes: .tr1 - Thermal resistance at location 1
    .tr2 - Thermal resistance at location 2
    .rsq1 - R squared value for the line fit used to determine the thermal resistance at location 1
    .rsq2 - R squared value for the line fit used to determine the thermal resistance at location 2
    .name - a string containing the name of the cycle derived from the name of the directory from which the Excel files were imported, i.e. 500 Cycles U
    .number - the number"""
    def __init__(self,cycle_number,tr_readings):
        self.tr1=tr_readings[0]
        self.tr2=tr_readings[1]
        self.rsq1=tr_readings[2]
        self.rsq2=tr_readings[3]
        self.td1=tr_readings[4]
        self.td2=tr_readings[5]
        self.name=cycle_number

    def __str__(self): return self.name

    def __repr_(self): return '<'+self.name+'>'

    def __cmp__(self, other):
        return cmp(int(re.search('(\d+)',self.name).group(1)),\
                int(re.search('(\d+)',other.name).group(1)))
    
    def number(self):
        return int(re.search('(\d+)(.+)',self.name).group(1))


def ReadFromExcel(filename):
    """Import data from an Excel file"""
    #Open the file for reading
    file=open(filename) 
    #Read the data from the file and store it into a variable called data
    #it is stored as a list of strings with each string contanining one line
    #from the original file
    data=file.readlines();
    #Close the file
    file.close()    
    #Split the strings into individual elements so that the data will be
    #a 2-d array rather than a 1-d list
    for i,v in enumerate(data):
        data[i]=string.split(data[i])
        for I,V in enumerate(data[i]):
            data[i][I]=float(data[i][I])
    return data 


def ExtractTemperatureColumns(data):
    """Select the desired colums from the imported data"""
    # transpose the data for that each column is an element in the array
    datatrans=numpy.transpose(data)
    # return columns 5, 6, 10, and 11
    return numpy.array([datatrans[4],datatrans[5],datatrans[9],datatrans[10]])
        


def FilterMeasurements(data):
    """Remove faulty or unnecessary readings from the list"""
    #Create a dummy list for putting data into
    new_array=[]
    #Check each value and exclude it if it is outside of a reasonable range
    for v in data:
        if v>0 and v<100:
            new_array=numpy.append(new_array,v)
    return new_array[-20:]
    

def AverageData(data):
    """Return the difference between the average reading of each
    thermistor/thermocouple pair"""
    # Average of (thermistor reading - thermocouple reading)
    try:
        TempDrop1=\
            numpy.mean(FilterMeasurements(data[0])-FilterMeasurements(data[1]))
    except ValueError:
        TempDrop1=-1
    try:
        TempDrop2=\
            numpy.mean(FilterMeasurements(data[2])-FilterMeasurements(data[3]))
    except ValueError:
        TempDrop2=-1
    return numpy.array([TempDrop1,TempDrop2])


def ProcessCycle(verbose=False):
    """Process the excel files in the current directory to get a thermal 
    resistance for the current cycle"""
    TemperatureDrops = numpy.zeros((5,2))
    power = x = [0, 0.5, 1.0, 1.5, 2.0]
    res = lambda c,y,x: y-c*x
    for i,file in enumerate(['W00.XLS','W05.XLS','W10.XLS','W15.XLS','W20.XLS']):
        data=ReadFromExcel(file)
        data=ExtractTemperatureColumns(data)
        TemperatureDrops[i]=(AverageData(data))
    if -1. in TemperatureDrops[:,0]:
        TR1 = ' '
        rsq1 = ' '
    else:
        y=TemperatureDrops[:,0]-TemperatureDrops[0,0]
        fit=scipy.optimize.leastsq(res, [6], args=(y,x))
        TR1 = fit[0]
        rsq1 = 1-sum([res(fit[0],y[i],x[i]) for i in range(1,5)])**2/sum(y[1:-1])**2
    if -1. in TemperatureDrops[:,1]:
        TR2 = ' '
        rsq2 = ' '
    else: 
        y=TemperatureDrops[:,1]-TemperatureDrops[0,1]
        fit=scipy.optimize.leastsq(res, [6], args=(y,x))
        TR2 = fit[0]
        rsq2 = 1-sum([res(fit[0],y[i],x[i]) for i in range(1,5)])**2/sum(y[1:-1])**2
    return [TR1, TR2, rsq1, rsq2, TemperatureDrops[:,0], TemperatureDrops[:,1]]


def CalculateClampedVsUnclamped(boards):
    """Calculates the absolute and percent differnece between the clamped and 
    unclamped reading for the non-overmolded boards"""
    for group in ['THER FR4','PSAK FR4','PSAK FLEX']:
        for board in boards.bytype(group):
            board.trd1={}
            for index,cycle in enumerate(board.cycles.clamped()[2:]):
                if cycle.tr1 != ' ' and board.cycles.unclamped()[index].tr1 != ' ':
                    diff=board.cycles.unclamped()[index].tr1-cycle.tr1
                    board.trd1[cycle.name]={'Difference':diff,'Percent Difference':diff/cycle.tr1}
            board.trd2={}
            for index,cycle in enumerate(board.cycles.clamped()[2:]):
                if cycle.tr2 != ' ' and board.cycles.unclamped()[index].tr2 != ' ':
                    diff=board.cycles.unclamped()[index].tr2-cycle.tr2
                    board.trd2[cycle.name]={'Difference':diff,'Percent Difference':diff/cycle.tr2}


def ImportData(basedir=DefaultBaseDirectory,verbose=False):
    """Import the the data from excel files and categorize it by the location
    of the files following the pattern where the first subfolder is the type 
    of the board, the second subfolder is the name of the board, the third 
    subfolder is the number of cycles and the fourth subfolder contains the 
    excel file with the meausrements"""
    # save the location of the current directory
    CurrentDirectory = os.getcwd()
    # move into the base directory
    os.chdir(basedir)
    # then into the data directory
    os.chdir('Data')
    # Initialize a variable containing an empty board list, which is an oject
    # of the class BoardList()
    boards=BoardList()
    # define a list a directories to ignore 
    dir_exclude_list=['CSV Files','Figures','November 08','TeX']
    # iterate through a loop for each directory not in the dir_exclude_list
    for directory in os.listdir(os.getcwd()):
        if (directory in dir_exclude_list) or (os.path.isdir(directory) == False):
            continue
        # assign the name of the current directory to be the type of the board
        BoardType=directory
        # move into the directory for the current type
        os.chdir(directory)
        # debugging 
        if verbose: print BoardType
        # iterate through for each subdirectory in the current directory
        for subdir in os.listdir(os.getcwd()):
            # assign the name of the current directory to be the name of
            # the board
            BoardName=subdir    
            # create a new object of the type Board() and append it to the
            # variable boards
            boards[BoardName]=Board(BoardType, BoardName)
            # move into the directory for the current board
            os.chdir(subdir)
            # debugging
            if verbose: print BoardName
            # iterate through for each subdirectory
            for subsubdir in sorted(os.listdir(os.getcwd())):
                # assign the name of the current directory to be the
                # name of the current cycle
                CycleNumber=subsubdir
                # debugging
                if verbose: print CycleNumber
                # move into the directory for the cycle
                os.chdir(subsubdir)
                # debugging
                if verbose: print os.getcwd()
                # append an object Cycle() to the attribute cycles
                # of the current board
                boards[BoardName].cycles.append(\
                        Cycle(CycleNumber,ProcessCycle()))
                # move up a directory to process the next cycle
                os.chdir(os.pardir)
            # sort the imported cycles
            boards[BoardName].cycles.sort()
            # move up a directory to process the next board
            os.chdir(os.pardir)
        # move up a directory to process the next board type
        os.chdir(os.pardir)
    # move back to the original directory
    os.chdir(CurrentDirectory)
    # clean up variables
    del(subdir, subsubdir, BoardType, BoardName)
    # fix any boards that were tested with the wires connected in the wrong order
    for cycle in [boards['THER8'].cycles[1],boards['PSAK-5 FLEX'].cycles[8]]:
        cycle.tr1, cycle.tr2 = cycle.tr2, cycle.tr1
    # Calculate Percent Differences for the thermal resistances after each cycle
    CalculateClampedVsUnclamped(boards)
    # return a list of boards with the thermal resistances as attributes stored
    # as a 2-D list in the location 
    # board.cycles = [[tr1,tr2,rsq1,rsq2],[tr1,tr2,rsq1,rsq2],...] 
    return boards


def LatexTable(data,filename='Table.tex',caption='default',label='default',\
        header='default',justification='default'):
    """Write a list to a .tex file in table format so that it can be included
    in a report"""

    # open the designated file name for writing, note: this will overwrite the 
    # previous contents of the file
    f=open(filename,'w')
    # set the default justification to be centered with vertical lines
    if justification == 'default': 
        justification = ('|c'*len(data.split('\n')[0].split('&')))+'|'
    f.write('\\begin{table}[htbp]\n\\label{%s}\n\\caption{%s}\n\\begin{center}\n\\begin{tabular}{%s}\n%s' % (label, caption, justification, \
        header+' \n'))
    f.write(data)
    f.write('\\end{tabular}\n\\end{center}\n\\end{table}\n')
    f.close()



def ExtractTRsForLatexTable(Boards,pub=False):
### Used in the function: CreateTRsLatexTable().  This take a list of boards, for instance all the THER FR4 boards, and return a string in latex format to be included as the body of one of the tables in Results.pdf
    l=[]
    for board in Boards:
        if pub:
            l.append([PubName(board.name),'$R_{jx_1}$'])
        else:
            l.append([board.name,'$R_{jx_1}$'])
        for i,v in enumerate(Boards[0].cycles.clamped()):
            if i >= len(board.cycles.clamped()):l[-1].append('')
            elif board.cycles.clamped()[i].tr1 == ' ': l[-1].append('')
            else: l[-1].append('%.2f' %board.cycles.clamped()[i].tr1)
        for i,v in enumerate(Boards[0].cycles.unclamped()):
            if i >= len(board.cycles.unclamped()):l[-1].append('')
            elif board.cycles.unclamped()[i].tr1 == ' ': l[-1].append('')
            else: l[-1].append('%.2f' %board.cycles.unclamped()[i].tr1)
        l[-1]='\t&\t'.join(l[-1])+'\\\\' 
        l.append([' '*(len(board.name)+17),'$R_{jx_2}$'])
        for i,v in enumerate(Boards[0].cycles.clamped()):
            if i >= len(board.cycles.clamped()): l[-1].append('')
            elif board.cycles.clamped()[i].tr2 == ' ': l[-1].append('')
            else: l[-1].append('%.2f' % board.cycles.clamped()[i].tr2)
        for i,v in enumerate(Boards[0].cycles.unclamped()):
            if i >= len(board.cycles.unclamped()): l[-1].append('')
            elif board.cycles.unclamped()[i].tr2 == ' ': l[-1].append('')
            else: l[-1].append('%.2f' % board.cycles.unclamped()[i].tr2)
        l[-1]='\t&\t'.join(l[-1])+'\\\\ '
    if 'OM' in Boards[0].type: average, standard_dev = FindStats(Boards)
    else: 
        average = FindStats(Boards,Exclude='Unclamped')[0]
        average.extend(FindStats(Boards,Exclude='Clamped')[0])
        standard_dev = FindStats(Boards,Exclude='Unclamped')[1]
        standard_dev.extend(FindStats(Boards,Exclude='Clamped')[1])
    l.append(['\\midrule\n  \multicolumn{2}{r}{Average} '])
    for number in average:
        l[-1].append('%.2f' % number)
    l[-1]='\t&\t'.join(l[-1])+'\\\\ '
    l.append(['\multicolumn{2}{r}{$\sigma$} '])
    for number in standard_dev:
        l[-1].append('%.2f' % number)
    l[-1]='\t&\t'.join(l[-1])+'\\\\ '
    return ' \n'.join(l)+'\\bottomrule \n'


def CreateTRsLatexTable(boards, filename='default'):
    """Generate a table in latex format including the 
    thermal resitances of each board for both the clamped and unclamped 
    configurations"""
    table=ExtractTRsForLatexTable(boards)
    columns=len(table.split('\n')[0].split('&'))
    readings=columns-2
    clampedreadings=len(boards[0].cycles.clamped())
    unclampedreadings=len(boards[0].cycles.unclamped())
    cyclenumbers=[]
    cycleunits=[]
    for cycle in boards[0].cycles.clamped():
        res=re.search('(\d+) (.+)',cycle.name)
        cyclenumbers.append(res.group(1))
        cycleunits.append(res.group(2))
    for cycle in boards[0].cycles.unclamped():
        res=re.search('(\d+) (.+)',cycle.name)
        cyclenumbers.append(res.group(1))
        cycleunits.append(res.group(2))
    if boards[0].type in ['PSAK FR4','PSAK FLEX','THER FR4']:
        head='\\toprule\n& & \\multicolumn{%d}{c}{Clamped} & \\multicolumn{%d}{c}{Unclamped}\\\\ \\cmidrule(r){3-%d} \\cmidrule(l){%d-%d}\n& & \\multicolumn{1}{c}{%s}\\\\ \n& %s\\\\ \\cmidrule{3-%d}\nBoard & & \\multicolumn{%d}{c}{$R_{jx}$ ($^{\circ}$C/W)}\\\\ \midrule' % (clampedreadings,unclampedreadings,2+clampedreadings,3+clampedreadings,2+clampedreadings+unclampedreadings,'} & \\multicolumn{1}{c}{'.join(cyclenumbers),' & \\multicolumn{1}{c}{Cycles} '*readings,columns, readings) 
    else:
        head='\\toprule\n& & \\multicolumn{1}{c}{%s}\\\\ \n& & \\multicolumn{1}{c}{%s}\\\\ \\cmidrule{3-%d}\nBoard & & \\multicolumn{%d}{c}{$R_{jx}$ ($^{\circ}$C/W)}\\\\ \midrule' % ('} & \\multicolumn{1}{c}{'.join(cyclenumbers),'} & \\multicolumn{1}{c}{'.join(cycleunits),columns, readings) 
    caption='Thermal resistance values for %s boards.' % PubName(boards[0].type)
    label='tab:%s' % boards[0].type.replace(' ','')
    justification='ll'+'r'*readings
    if filename == 'default':
        filename='%sThermalResistanceTable.tex' % boards[0].type.replace(' ','')
    LatexTable(table,filename=filename,header=head,caption=caption,label=label,justification=justification)



def CreateTables(boards,basedir=DefaultBaseDirectory,pub=False):
    """Apply the CreateTRsLatexTable() function for each type of board
    and save the resulting files to the appropriate location"""
    if pub:
        os.chdir(ipackdir)
        table_dir='Tables'
    else:
        os.chdir(basedir)
        table_dir=os.path.join('Results','Tables')
    list_of_tables=[]
    if not os.path.exists(table_dir): 
        os.makedirs(table_dir)  
    os.chdir(table_dir)
    for board_group in boards.bytype():
        filename='%sThermalResistancesTable.tex' % board_group[0].type.replace(' ','')
        CreateTRsLatexTable(board_group, filename=filename)
        list_of_tables.append(filename)
    os.chdir(os.pardir)
    f=open('Tables.tex','w')
    for table in list_of_tables:
        f.writelines('\\input{Tables/%s}\n' % table)
    f.close()
    os.chdir(basedir)


def ExtractTRsForCSVFile(Boards):
    """Build a comma separated string for use in CreateCSVFiles()"""
    l=[]
    for board in Boards:
        l.append([board.name,'TR1'])
        for cycle in board.cycles.clamped():
            if cycle.tr1 == ' ': l[-1].append('    ')
            else: l[-1].append('%f' % cycle.tr1)
        for cycle in board.cycles.unclamped():
            if cycle.tr1 == ' ': l[-1].append('    ')
            else: l[-1].append('%f' % cycle.tr1)
        l[-1]=','.join(l[-1]) 
        l.append([board.name,'TR2'])
        for cycle in board.cycles.clamped():
            if cycle.tr2 == ' ': l[-1].append('    ')
            else: l[-1].append('%f' % cycle.tr2)
        for cycle in board.cycles.unclamped():
            if cycle.tr2 == ' ': l[-1].append('    ')
            else: l[-1].append('%f' % cycle.tr2)
        l[-1]=','.join(l[-1])
    return ' \n'.join(l)


def CreateCSVFiles(boards,basedir=DefaultBaseDirectory):
    """Creates a CSV file with the processed thermal resistances"""
    OriginalDirectory=os.getcwd()
    os.chdir(basedir)
    csv_dir=os.path.join('Results','CSV Files')
    if not os.path.exists(csv_dir): 
        os.makedirs(csv_dir)    
    os.chdir(csv_dir)
    for board_group in boards.bytype():
        filename='%s.csv' % board_group[0].type
        f=open(filename,'w')
        f.write(ExtractTRsForCSVFile(board_group))
        f.close()
    f=open('AllBoards.csv','w')
    f.write(ExtractTRsForCSVFile(boards.all()))
    f.close()
    os.chdir(OriginalDirectory)


def FindStats(Boards,Exclude='',verbose=False,ClampedThenUnclamped=False):
    """Returns two arrays.  The first array give the average resistance for 
    each cycle and the second array gives the corresponding standard deviation.  
    The convention for this fucntion is to use the options:
    Exclude='Unclamped' - to get the values fo the clamped boards
    Exclude='Clamped' to get the values for the unclamped boards.  
    This convention is kept to prevent breaking code that was written in the 
    first version of this script."""
    data=[]
    datacheck=True
    for board in Boards:
        templist=[]
        for cycle in board.cycles:
            if Exclude=='Unclamped' and ' U' in cycle.name: continue
            if Exclude=='Clamped' and ' U' not in cycle.name: continue
            elif cycle.tr1 == ' ': datacheck=False
            else: templist.append(cycle.tr1)
        if datacheck: data.append(templist)
        datacheck=True
        templist=[]
        for cycle in board.cycles:
            if Exclude=='Unclamped' and ' U' in cycle.name: continue
            if Exclude=='Clamped' and ' U' not in cycle.name: continue
            if cycle.tr2 == ' ': datacheck=False
            else: templist.append(cycle.tr2)
        if datacheck: data.append(templist)
        datacheck=True
    data=numpy.array(data).transpose()

    average=[numpy.mean(data[i]) for i in range(len(data))]
    deviation=[numpy.std(data[i]) for i in range(len(data))]
    return average, deviation


def PubName(real_name):
    """Removes identifying terminology from the labels for 
    the purpose of IPACK2009-89097"""

    if 'THER' in real_name:
        return re.compile('THER').sub('ALT',real_name)
    if 'PSAK' in real_name:
        return re.compile('PSAK').sub('PSA',real_name)  
    if 'PSAH' in real_name: 
        if '682' in real_name:
            return re.compile('PSAH').sub('PSA',re.compile('682').sub('-B',real_name))
        if '633' in real_name:
            return re.compile('PSAH').sub('PSA',re.compile('633').sub('-A',real_name))  
        return re.compile('PSAH').sub('PSA',real_name)
    return real_name


def CreateGraphs(boards, basedir=DefaultBaseDirectory,figuredir='',pub=False):
    """Creates the graphs to be include in Result.pdf, IPACK2009-89097, and thesis"""

    ClampedCycles=[0,250,500,750,1000,1250,1500]
    UnClampedCycles=[500,750,1000,1250,1500]
    
    OriginalDirectory=os.getcwd()

    rcParams['figure.figsize']=(4.5, 4.5/1.61803)
    rcParams['font.size']=10.0
    rcParams['legend.fontsize']='x-small'
    rcParams['ytick.labelsize']='small'
    rcParams['xtick.labelsize']='small'
    rcParams['lines.linewidth']=1.0
    rcParams['axes.labelsize']='medium'
    rcParams['text.usetex']='True'
    rcParams['patch.linewidth']=0.1
    rcParams['legend.shadow']='False'
    rcParams['legend.columnspacing']=2.5
    rcParams['legend.handletextpad']=0.2
    rcParams['text.latex.preamble']='\usepackage{pslatex},\usepackage{bm}'
    
    if pub:
        os.chdir(ipackdir)
        fig_dir='Figures'
        #rcParams['text.latex.preamble']='\usepackage{pslatex},\usepackage{bm}'
        rcParams['figure.figsize']=(3.5,3.5/1.61803)
    else:
        os.chdir(basedir)
        fig_dir=os.path.join('Results','Figures',figuredir)
        #rcParams['text.latex.preamble']='\usepackage{bm}'

    if not os.path.exists(fig_dir): 
        os.makedirs(fig_dir)    
    os.chdir(fig_dir)
    
    tr={}
    std={}
    for group in boards.bytype():
        stats=FindStats(group,Exclude='Unclamped')
        tr[group[0].type]=stats[0]
        std[group[0].type]=stats[1]
    Color={'THER FR4':'grey', 'PSAK FLEX':'orange', 'PSAK FR4':'green', 'PSAH OM633':'blue', 'PSAH OM682':'brown'}
    LineStyle={'THER FR4':'-', 'PSAK FLEX':'-', 'PSAK FR4':'-', 'PSAH OM633':'--', 'PSAH OM682':'--'}

    AllTypes=['THER FR4','PSAK FR4','PSAK FLEX','PSAH OM633','PSAH OM682']
    UnClampedTypes=['THER FR4','PSAK FR4','PSAK FLEX']
    
####### Thermal Resistance for each type of non-overmolded board with cycling
    AllBoardsFigure=plt.figure()
    AllBoardsFigure.clf()
    Allax=plt.axes([0.125,0.135,1-0.21,1-0.2])
    
    for type in ['THER FR4','PSAK FR4','PSAK FLEX']:
        cyc=ClampedCycles
        if pub:
            Allax.errorbar(cyc,tr[type],yerr=std[type],color=Color[type],label=r'\textrm{'+PubName(type)+'}',antialiased='True',capsize=2)
        else:
            Allax.errorbar(cyc,tr[type],yerr=std[type],color=Color[type],label=r'\textrm{'+type+'}',antialiased='True',capsize=2)

    Allax.axis([-50,1600,0,10]) # May need updating
    xlab=Allax.set_xlabel(r'\textbf{Cycles}')
    Allax.set_ylabel(r'\(\bm{R}_{\bm{jx}}\) \textbf{(\(^{\bm{\circ}}\)C/W)}')
    Allax.set_title=(r'Thermal Resistance with Cycling')
    lg=Allax.legend(shadow=False)   
    lg.legendPatch.set_alpha(0.5)
    AllBoardsFigure.savefig('ThermalResistancesAllNonOvermoldedBoards.pdf', transparent=True)
    del(Allax,AllBoardsFigure)
    
####### Thermal Resistance for each type of overmolded board with cycling
    AllBoardsFigure=plt.figure()
    AllBoardsFigure.clf()
    Allax=plt.axes([0.125,0.135,1-0.2,1-0.2])
    
    for type in ['PSAH OM633','PSAH OM682']:
        if pub:
            Allax.errorbar(cyc,tr[type],yerr=std[type],linestyle=LineStyle[type],color=Color[type],label=r'\textrm{'+PubName(type)+'}',antialiased='True')
        else:
            Allax.errorbar(cyc,tr[type],yerr=std[type],linestyle=LineStyle[type],color=Color[type],label=r'\textrm{'+type+'}',antialiased='True')

    Allax.axis([-50,1600,0,10]) # May need updating
    xlab=Allax.set_xlabel(r'\textbf{Cycles}')
    Allax.set_ylabel(r'\(\bm{R}_{\bm{jx}}\) \textbf{(\(^{\bm{\circ}}\)C/W)}')
    Allax.set_title=(r'Thermal Resistance with Cycling')
    lg=Allax.legend(shadow=False)   
    lg.legendPatch.set_alpha(0.5)
    AllBoardsFigure.savefig('ThermalResistancesAllOvermoldedBoards.pdf', transparent=True)
    del(Allax,AllBoardsFigure)

####### Thermal Resistance for each type board with cycling
    AllBoardsFigure=plt.figure()
    AllBoardsFigure.clf()
    Allax=plt.axes([0.15,0.15,1-0.22,1-0.2])
    
    for type in AllTypes:
        cyc={'THER FR4':[0,250,500,750,1000,1250,1500],'PSAK FLEX':[0,250,500,750,1000,1250,1500],'PSAK FR4':[0,250,500,750,1000,1250,1500],'PSAH OM682':[0,250,500,750,1000,1250,1500],'PSAH OM633':[0,250,500,750,1000,1250,1500]}
        if pub:
            Allax.errorbar(cyc[type],tr[type],yerr=0.25,linestyle=LineStyle[type],color=Color[type],label=r'\textrm{'+PubName(type)+'}',antialiased='True')
        else:
            Allax.errorbar(cyc[type],tr[type],yerr=0.25,linestyle=LineStyle[type],color=Color[type],label=r'\textrm{'+type+'}',antialiased='True')

    Allax.axis([-50,1600,1,7]) # May need updating
    Allax.set_xticks([0,250,500,750,1000,1250,1500]) # May need updating
    Allax.set_yticks([2,4,6])
    xlab=Allax.set_xlabel(r'\textbf{Cycles}')
    Allax.set_ylabel(r'\(\bm{R}_{\bm{jx}}\) \textbf{(\(^{\bm{\circ}}\)C/W)}')
    Allax.set_title=(r'Thermal Resistance with Cycling')
    lg=Allax.legend(shadow=False,loc=3,ncol=2)  
    lg.legendPatch.set_alpha(0.5)
    AllBoardsFigure.savefig('ThermalResistancesAllBoards.pdf', transparent=True)
    del(Allax,AllBoardsFigure)

####### Average change in junction resistance of clamped boards with cycling
    AllBoardsChangeFigure=plt.figure()
    ax=plt.axes([0.15,0.15,1-0.22,1-0.2])

    for type in AllTypes:
        if pub:
            ax.plot(cyc[type],[i-tr[type][0] for i in tr[type]],linestyle=LineStyle[type],color=Color[type],label=r'\textrm{'+PubName(type)+'}',antialiased='True')
        else:
            #ax.plot(cyc[type],[i-tr[type][0] for i in tr[type]],linestyle=LineStyle[type],color=Color[type],label=r'\textrm{'+type+'}',antialiased='True')
            ax.plot(cyc[type],[i-tr[type][0] for i in tr[type]],linestyle=LineStyle[type],color=Color[type],antialiased='True')
    leg1=ax.plot([1],linewidth=1, color=Color['THER FR4'], linestyle=LineStyle['THER FR4'])
    leg2=ax.plot([1],linewidth=1, color=Color['PSAK FR4'], linestyle=LineStyle['PSAK FR4'])
    leg3=ax.plot([1],linewidth=1, color=Color['PSAK FLEX'], linestyle=LineStyle['PSAK FLEX'])
    leg4=ax.plot([1],linewidth=1, color=Color['PSAH OM633'], linestyle=LineStyle['PSAH OM633'])
    leg5=ax.plot([1],linewidth=1, color=Color['PSAH OM682'], linestyle=LineStyle['PSAH OM682'])
    ax.axis([-50,1600,-0.8,0.2]) # May need updating
    ax.set_xticks([0,250,500,750,1000,1250,1500]) # May need updating
    ax.set_yticks([-.8,-.6,-0.4,-0.2,-0,0.2])
    ax.set_xlabel(r'\textbf{Cycles}')
    ax.set_ylabel(r'\(\bm{\Delta R}_{\bm{jx}}\) \textbf{(\(^{\bm{\circ}}\)C/W)}')
    lg=ax.legend((leg1,leg2,leg3,leg4,leg5),('THER FR4 (35 locations)','PSAK FR4 (18 locations)','PSAK FLEX (18 locations)','PSAH OM633 (8 Locations)','PSAH OM682 (10 locations)'),'lower left',shadow=False)
    #lg=ax.legend(shadow=False,loc=3,ncol=2) 
    lg.legendPatch.set_alpha(0.5)
    AllBoardsChangeFigure.savefig('ChangeInThermalResistancesAllBoards.pdf', transparent=True)
    del(ax,AllBoardsChangeFigure)

####### Sample plot of the difference between clamped and unclamped readings
    ClampedvsUnclamped=plt.figure()
    ClampedvsUnclamped.clf()
    axCvsUnc=plt.axes([0.15,0.15,1-0.22,1-0.2])
    a={'name':'THER14','location':'tr2','color':'#FF0000','label':'Full Delam.'}
    b={'name':'THER10','location':'tr1','color':'#33FF00','label':'No Delam.'}
    c={'name':'THER12','location':'tr1','color':'orange','label':'Partial Delam.'}
    
    leg={'Full Delam.':{},'Partial Delam.':{},'No Delam.':{}}
    for board in [a,b,c]:
        if board['location']=='tr1':
            clampedtrs=[cycle.tr1 for cycle in boards[board['name']].cycles.clamped() if cycle.name != '250 Cycles']
            unclampedtrs=[cycle.tr1 for cycle in boards[board['name']].cycles.unclamped()]
            unclampedtrs.insert(0,clampedtrs[0])
        elif board['location']=='tr2':
            clampedtrs=[cycle.tr2 for cycle in boards[board['name']].cycles.clamped() if cycle.name != '250 Cycles']
            unclampedtrs=[cycle.tr2 for cycle in boards[board['name']].cycles.unclamped()]
            unclampedtrs.insert(0,clampedtrs[0])
        plotcycles=[0]
        plotcycles.extend(UnClampedCycles)
        axCvsUnc.plot(plotcycles,unclampedtrs,linestyle='--',color=board['color'],marker='o',markersize=4)
        leg[board['label']]['uc']=axCvsUnc.plot([1],linestyle='--',color=board['color'])
        axCvsUnc.plot(plotcycles,clampedtrs,linestyle='-',color=board['color'],marker='o',markersize=4)
        leg[board['label']]['c']=axCvsUnc.plot([1],linestyle='-',color=board['color'])
    
    blanka=axCvsUnc.plot([1],visible=False)
    blankb=axCvsUnc.plot([1],visible=False)
    blankc=axCvsUnc.plot([1],visible=False)
    blankd=axCvsUnc.plot([1],visible=False)
    blanke=axCvsUnc.plot([1],visible=False)
    blankf=axCvsUnc.plot([1],visible=False)

    axCvsUnc.axis([-50,1600,0,13]) # May need updating
    axCvsUnc.set_xticks([0,250,500,750,1000,1250,1500]) # May need updating
    axCvsUnc.set_yticks([0,2,4,6,8,10,12])
    axCvsUnc.set_xlabel(r'\textbf{Cycles}')
    axCvsUnc.set_ylabel(r'\(\bm{ R}_{\bm{jx}}\) \textbf{(\(^{\bm{\circ}}\)C/W)}')
    lg=axCvsUnc.legend((blanka,leg['Full Delam.']['c'],leg['Full Delam.']['uc'],blankb,blankc,leg['Partial Delam.']['c'],leg['Partial Delam.']['uc'],blankd,blanke,leg['No Delam.']['c'],leg['No Delam.']['uc'],blankf),(r'\underline{Full Delam.}','Clamped','Unclamped',r'(THER14)',r'\underline{Partial Delam.}','Clamped','Unclamped',r'(THER12)',r'\underline{No Delam.}','Clamped','Unclamped',r'(THER10)'),shadow=False,loc=3,ncol=3,columnspacing=2.5,handletextpad=0.2) 
    lg.legendPatch.set_alpha(0.5)
    ClampedvsUnclamped.savefig('ClampedVsUnclampedGraph.pdf', transparent=True)
    

####### Delam Plot
    for Type in UnClampedTypes:
        DelamPlotAll=plt.figure()
        DelamPlotAll.clf()
        axall=plt.axes([0.15,0.15,1-0.22,1-0.2])
            
        FullDelam=0.5
        ParDelam=0.25
        
        def DelamLineColor(pd):
            if pd < ParDelam: return '#33FF00'
            elif pd < FullDelam: return 'orange'
            else: return '#FF0000'
        
        for board in boards.bytype(Type):
            if board.name == 'THER19': continue
            if  board.name != 'PSAK-5 FLEX':
                pds1=[0]
                cyc=[0]
                for cycle in board.cycles.clamped()[2:]:
                    pds1.append(board.trd1[cycle.name]['Percent Difference']*100)
                    cyc.append(cycle.number())
                    pds=[pds1[-1]]
                    axall.scatter([cycle.number()],pds,color='black',s=20,marker='o')
                    axall.scatter([cycle.number()],pds,color=DelamLineColor(pds1[-1]/100.),s=10,marker='o')
                axall.plot(cyc,pds1,color='black',linestyle='-',linewidth=0.25)

            if  board.name != 'PSAK-2 FLEX' and board.name != 'PSAH OM633-3' and board.name != 'PSAK-5 FLEX':
                pds2=[0]
                cyc=[0]
                for cycle in board.cycles.clamped()[2:]:
                    pds2.append(board.trd2[cycle.name]['Percent Difference']*100)
                    cyc.append(cycle.number())
                    pds=[pds2[-1]]
                    axall.scatter([cycle.number()],pds,color='black',s=20,marker='o')
                    axall.scatter([cycle.number()],pds,color=DelamLineColor(pds2[-1]/100.),s=10,marker='o')
                axall.plot(cyc,pds2,color='black',linestyle='-',linewidth=0.25)

        axall.plot((0,10000),(FullDelam*100,FullDelam*100),linestyle='--',linewidth=0.5,color='k')
        axall.plot((0,10000),(ParDelam*100,ParDelam*100),linestyle='--',linewidth=0.5,color='k')
        
        axall.axis([-50,1600,-15,185]) # May need updating
        axall.set_xticks([0,500,750,1000,1250,1500]) # May need updating
        axall.set_yticks([0,25,50,75,100,125,150,175]) # May need updating
        xlab=axall.set_xlabel(r'\textbf{Cycles}')
        axall.set_ylabel(r'\textbf{\% Difference in $\,\bm{R_{\bm{jx}}}$}')
        DelamPlotAll.savefig('delamplot%s.pdf'%Type.replace(' ',''),transparent=True)

####### Bar plot
    BarPlot=plt.figure()
    BarPlot.clf()
    ax=plt.axes([0.15,0.15,1-0.2,1-0.2])
    
    full={}
    partial={}
    no={}
    width=0.2
    for i,Type in enumerate(['THER FR4','PSAK FR4','PSAK FLEX']):
        full[Type]=numpy.array([v[0] for k,v in sorted(DelaminationData(boards)[Type].items())])
        full['PSAK FR4']=numpy.array([0,0,0,0,0,0]) # May need updating
        full['PSAK FLEX']=numpy.array([0,0,0,0,0,0]) # May need updating
        full['THER FR4']=numpy.array([0,7/35.,8/35.,12/35.,10/35.,12/35.]) # May need updating
        partial[Type]=numpy.array([v[1] for k,v in sorted(DelaminationData(boards)[Type].items())])
        partial['PSAK FR4']=numpy.array([0,0,0,0,0,0]) # May need updating
        partial['PSAK FLEX']=numpy.array([0,0,0,0,0,0]) # May need updating
        partial['THER FR4']=numpy.array([0,7/35.,6/35.,5/35.,7/35.,4/35.]) # May need updating
        no[Type]=numpy.array([v[2] for k,v in sorted(DelaminationData(boards)[Type].items())])
        no['PSAK FR4']=numpy.array([18./18.,18./18.,18./18.,18./18.,18./18.,18./18.]) # May need updating
        no['PSAK FLEX']=numpy.array([18./18.,18./18.,18./18.,18./18.,18./18.,18./18.]) # May need updating
        no['THER FR4']=numpy.array([35/35.,21/35.,21/35.,18/35.,18/35.,19./35.]) # May need updating
        
        ind=numpy.arange(len(full[Type]))
        NoDelam=ax.bar(ind+i*width,no[Type],width,color='#33FF00')
        ParDelam=ax.bar(ind+i*width,partial[Type],width,color='orange',bottom=no[Type])
        FullDelam=ax.bar(ind+i*width,full[Type],width,color='#FF0000',bottom=no[Type]+partial[Type])
    
    ax.axis([-.1,4,0,1.5]) # May need updating
    
    FontSize=6
    Rotation=90
    Offset=0.075
    yOffset=.01
    for i in [0,1,2,3,4,5]:
        if pub == True:
            ax.text(0+Offset+i,yOffset,PubName('THER FR4'),rotation=Rotation,fontsize=FontSize)
            ax.text(width+Offset+i,yOffset,PubName('PSAK FR4'),rotation=Rotation,fontsize=FontSize)
            ax.text(width*2+Offset+i,yOffset,PubName('PSAK FLEX'),rotation=Rotation,fontsize=FontSize)
        else:
            ax.text(0+Offset+i,yOffset,'THER FR4',rotation=Rotation,fontsize=FontSize)
            ax.text(width+Offset+i,yOffset,'PSAK FR4',rotation=Rotation,fontsize=FontSize)
            ax.text(width*2+Offset+i,yOffset,'PSAK FLEX',rotation=Rotation,fontsize=FontSize)
   
    
    ax.set_xticks(numpy.array([0,1,2,3,4,5,6])) # May need updating
    ax.set_yticks(numpy.array([0,.25,.5,.75,1]))
    ax.set_xticklabels((0,500,750,1000,1250,1500)) # May need updating
    ax.set_yticklabels((0,25,50,75,100))
    ax.set_ylabel(r'\textbf{Percentage of Locations}')
    ax.set_xlabel(r'\textbf{Cycles}')
    lg=ax.legend((NoDelam[0],ParDelam[0],FullDelam[0]),('No Delamination','Parital Delamination','Full Delamination'),shadow=False)
    lg.legendPatch.set_alpha(0.5)
    
    BarPlot.savefig('barplotpercent.pdf',transparent=True)


def DisplayTRs(Boards):
    """Display Thermal Resistances for the boards.  
    This is for use in the interactive python shell for debugging purposes"""
    for Type in Boards.types():
        print Type
        for board in Boards.bytype(Type):
            l=[]
            l.append(board.name)
            for cycle in board.cycles.clamped():
                if type(cycle.tr1)==numpy.float64:
                    l.append('%.2f' % cycle.tr1)
                else:
                    l.append('   ')
            l.append('|')
            for cycle in board.cycles.unclamped():
                if type(cycle.tr1)==numpy.float64:
                    l.append('%.2f' % cycle.tr1)
                else:
                    l.append('   ')
            print '\t'.join(l)
            l=[]
            l.append(' '*len(board.name))
            for cycle in board.cycles.clamped():
                if type(cycle.tr2) == numpy.float64:
                    l.append('%.2f' % cycle.tr2)
                else:
                    l.append('   ')
            l.append('|')
            for cycle in board.cycles.unclamped():
                if type(cycle.tr2) == numpy.float64:
                    l.append('%.2f' % cycle.tr2)
                else:
                    l.append('   ')
            print '\t'.join(l)


def DisplayPDs(Boards):
    """Display percent difference between the thermal resitances of the clamped
     and unclamped boards.  
    This is for use in the interactive python shell for debugging purposes"""
    for Type in ['THER FR4','PSAK FR4','PSAK FLEX']:
        print Type
        for board in Boards.bytype(Type):
            l=[]
            l.append(board.name)
            for index,cycle in enumerate(board.cycles.clamped()[2:]):
                if cycle.tr1 != ' ' and board.cycles.unclamped()[index].tr1 != ' ': 
                    l.append('%.2f' % board.trd1[cycle.name]['Percent Difference'])
                else:
                    l.append('   ')
            print '\t'.join(l)
            l=[]
            l.append(' '*len(board.name))
            for index,cycle in enumerate(board.cycles.clamped()[2:]):
                if cycle.tr2 != ' ' and board.cycles.unclamped()[index].tr2 != ' ': 
                    l.append('%.2f' % board.trd2[cycle.name]['Percent Difference'])
                else:
                    l.append('   ')
            print '\t'.join(l)


def DisplayTRDs(Boards):
    """Display the difference between the thermal resistances of the clamped
    and unclamped boards.  
    This is for use in the interactive python shell for debugging purposes"""
    for Type in ['THER FR4','PSAK FR4','PSAK FLEX']:
        print Type
        for board in Boards.bytype(Type):
            l=[]
            l.append(board.name)
            for index,cycle in enumerate(board.cycles.clamped()[2:]):
                if cycle.tr1 != ' ' and board.cycles.unclamped()[index].tr1 != ' ': 
                    l.append('%.2f' % board.trd1[cycle.name]['Difference'])
                else:
                    l.append('   ')
            print '\t'.join(l)
            l=[]
            l.append(' '*len(board.name))
            for index,cycle in enumerate(board.cycles.clamped()[2:]):
                if cycle.tr2 != ' ' and board.cycles.unclamped()[index].tr2 != ' ': 
                    l.append('%.2f' % board.trd2[cycle.name]['Difference'])
                else:
                    l.append('   ')
            print '\t'.join(l)


def DelaminationData(Boards):
    """Display the number of boards for each degree of delamination for each cycle.  
    This is to be used in the interactive shell and is not currently incorporated 
    into any other function definitions"""
    # Criteria for delamination
    full_delam = 0.5
    partial_delam =0.25
    delam_data={}
    for group in Boards.bytype():
        if ' OM' in group[0].type:
            continue
        delam_data[group[0].type]={}
        for index,cycle in enumerate(group[0].cycles.clamped()[2:]):
            number_of_full_delam=0
            number_of_partial_delam=0
            number_of_no_delam=0
            for board in group:
                if board.cycles.clamped()[index+2].tr1 != ' ' and board.cycles.unclamped()[index].tr1 != ' ' and board.name != 'PSAK-5 FLEX': 
                    pd=board.trd1[cycle.name]['Percent Difference']
                    if pd >= full_delam: number_of_full_delam+=1
                    elif pd >= partial_delam: number_of_partial_delam+=1
                    else: number_of_no_delam+=1
                if board.cycles.clamped()[index+2].tr2 != ' ' and board.cycles.unclamped()[index].tr2 != ' ': 
                    pd=board.trd2[cycle.name]['Percent Difference']
                    if pd >= full_delam: number_of_full_delam+=1
                    elif pd >= partial_delam: number_of_partial_delam+=1
                    else: number_of_no_delam+=1
            delam_data[group[0].type][cycle.name]=(number_of_full_delam,number_of_partial_delam,number_of_no_delam)
    return delam_data
            


if __name__ == '__main__':
    boards = ImportData()
    CreateTables(boards)
    CreateCSVFiles(boards)
    CreateGraphs(boards)
    os.chdir(os.path.join(DefaultBaseDirectory,'Results'))
    os.system('pdflatex Results.tex')
    os.system('pdflatex Results.tex')
    #CreateTables(boards,pub=True)
    #CreateGraphs(boards,pub=True)
    #os.chdir(ipackdir)
    #os.system('pdflatex IPACK2009-89097.tex')
    #os.system('pdflatex IPACK2009-89097.tex')

