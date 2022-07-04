import os
from tkinter import *
from tkinter import ttk
from tkinter import filedialog as fd
from tkinter.messagebox import showinfo
import shutil
import sys
import json
from tkinter import messagebox
from turtle import width

sys.path.insert(0,'./python')
from setting import out_dir, video_dir
from run import extractingFrames, predictValidFrames, extractCodeRegions, CorrectingErrors, deleteTempFiles, checkOutDir
import pathlib


class StdoutRedirector(object):

    def __init__(self, text_area):
        self.text_area = text_area

    def write(self, str):
        self.text_area.insert(END, str)
        self.text_area.see(END)
        root.update_idletasks() 



def deleteItem():
    selected_checkboxs = videoList.curselection()
    for selected_checkbox in selected_checkboxs[::-1]:
        os.remove(os.path.join(video_dir,videoList.get(selected_checkbox)))
        videoList.delete(selected_checkbox)   

def copyItem(filename):
    shutil.copy(filename, video_dir)
    videoList.delete(0, END)
    myList = os.listdir(video_dir)
    for file in myList:
        videoList.insert(END, file)


def select_file():


    filetypes = (
        ('video files', '*.webm *.mkv *.avi *.mp4 *.m4p *.svi'),
        ('All files', '*.*')
    )

    filename = fd.askopenfilename(
        title='Open a file',
        initialdir='/home/%s'%os.environ.get("USERNAME"),
        filetypes=filetypes)

    copyItem(filename)

    showinfo(
        title='Selected File',
        message=filename
    )

def startRunning():
    selected_checkboxs = videoList.curselection()
    for selected_checkbox in selected_checkboxs[::-1]:
        try:
            console.delete('1.0', END)
            videoName = videoList.get(selected_checkbox)
            if checkOutDir(videoName) == "True":
                console.insert(END,'%s.json Already Exists in Out Directory\n'% videoName.rsplit('.', 1)[0],'WARN')

            elif checkOutDir(videoName) == "False":
                deleteTempFiles(videoName)
                console.insert(END,'Reducing Non-Informative Frames ....\n','INFO')
                console.see(END)
                root.update_idletasks() 
                extractingFrames(videoName)
                pb1['value'] += 25
                root.update_idletasks() 
                console.insert(END, '\nRemoving Non-Code and Noisy-Code Frames ....\n','INFO')
                console.see(END)
                root.update_idletasks() 
                predictValidFrames(videoName) 
                pb1['value'] += 25        
                root.update_idletasks() 
                console.insert(END, '\nDistinguishing Code versus Non-Code Regions ....\n','INFO')
                console.see(END)
                root.update_idletasks()
                extractCodeRegions(videoName)
                pb1['value'] += 25 
                root.update_idletasks()
                console.insert(END, '\nGet OCRed Source Code and Correcting Erroes ....\n','INFO')
                console.see(END)
                root.update_idletasks()
                CorrectingErrors(videoName)
                pb1['value'] += 25 
                root.update_idletasks()

        except Exception as e:
            raise e 

        finally:
            pb1['value'] = 0 
            goBack()
            currentPath.set(defultPath.get())


def showJsonFile(path):
    global top, frames_length, current_frame, current_index
    
    with open(path) as json_file:
        data = json.load(json_file)
        

    current_index = 0
    frames_length = len(data['frames'])
    current_frame = data['frames'][current_index]

    options = [str(i[0]) + ' ' + str(i[2]) for i in data['frames']]

    def next():
        global current_index, frames_length, current_frame 
        if current_index < frames_length -1:
            current_index += 1
        else:
            current_index = 0

        current_frame = data['frames'][current_index]
        Content.delete('1.0', END)
        Content.insert(END, current_frame[1])
        FrameNumber.current(current_index)



    def previous():
        global current_index, frames_length, current_frame 
        if current_index > 0:
            current_index -= 1
        else: 
            current_index = frames_length -1

        current_frame = data['frames'][current_index]
        Content.delete('1.0', END)
        Content.insert(END, current_frame[1])
        FrameNumber.current(current_index)

    def copyContent():
        content = Content.get("1.0",'end-1c')
        top.clipboard_clear()
        top.clipboard_append(content)

    def on_closing():
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            root.deiconify()
            console.delete('1.0', END)
            top.destroy()

    def changeFrame(event):
        global current_index, current_frame 
        current_index = FrameNumber.current()
        current_frame = data['frames'][current_index]
        Content.delete('1.0', END)
        Content.insert(END, current_frame[1])
        

    top = Toplevel(root)
    top.title(data['name'])
    top.resizable(False, False)

    window_width = 500
    window_height = 200
        # get the screen dimension
    screen_width = top.winfo_screenwidth()
    screen_height = top.winfo_screenheight()

        # find the center point
    center_x = int(screen_width/2 - window_width / 2)
    center_y = int(screen_height/2 - window_height / 2)

        # set the position of the window to the center of the screen
    top.geometry("+%d+%d"%(center_x, center_y))

    NextFrame = Button(top, text='Next Frame', command=next, width=15, height=2)
    NextFrame.grid(
        row=0, column=3, sticky='we'
    )
    FrameNumber = ttk.Combobox(top, values=options,
     state='readonly', width=7)
    FrameNumber.current(0)
    FrameNumber.bind('<<ComboboxSelected>>', changeFrame)
    FrameNumber.grid(
        row=0, column=2, sticky='we', padx=5
    )

    FrameLabel = Label(top, text="Frame:", width=7)
    FrameLabel.grid(
        row=0, column=1, sticky='we'
    )

    PreviousFrame = Button(top, text='Previous Frame', command=previous, width=15, height=2)
    PreviousFrame.grid(
        row=0, column=0, sticky='we'
    )
    Content = Text(top, height=15)
    Content.grid(
        row=2, column=0, sticky='we', columnspan=4
    )
    Content.insert(END, current_frame[1])

    CopyContent = Button(top, text='Copy Content', command=copyContent, height=2)
    CopyContent.grid(
        row=3, column=0, sticky='we', columnspan=4
    )

    top.protocol("WM_DELETE_WINDOW", on_closing)


top = ''
current_index = None
frames_length = None
current_frame = None

def pathChange(*event):
    # Get all Files and Folders from the given Directory
    directory = os.listdir(currentPath.get())
    # Clearing the list
    list.delete(0, END)
    # Inserting the files and directories into the list
    for file in directory:
        list.insert(0, file)

def changePathByClick(event=None):
    # Get clicked item.
    picked = list.get(list.curselection()[0])
    # get the complete path by joining the current path with the picked item
    path = os.path.join(currentPath.get(), picked)
    # Check if item is file, then open it
    if os.path.isfile(path):
        try:
            root.withdraw()
            showJsonFile(path)

        except Exception as e:
            root.deiconify()
            raise e
        
    # Set new path, will trigger pathChange function.
    else:
        currentPath.set(path)

def goBack(event=None):
    # get the new path
    newPath = pathlib.Path(currentPath.get()).parent
    # set it to currentPath
    currentPath.set(newPath)
    # simple message







 
# create the root window
root = Tk()
root.title('PSC2CODE')
root.resizable(False, False)
window_width = 800
window_height = 600
# get the screen dimension
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# find the center point
center_x = int(screen_width/2 - window_width / 2)
center_y = int(screen_height/2 - window_height / 2)

# set the position of the window to the center of the screen
root.geometry("%dx%d+%d+%d"%(window_width,window_height, center_x, center_y))


# String variables
defultPath = currentPath = StringVar(
    root,
    name='defultPath',
    value= out_dir
)
currentPath = StringVar(
    root,
    name='currentPath',
    value= defultPath.get()
)
# Bind changes in this variable to the pathChange function
currentPath.trace('w', pathChange)


 
pw = ttk.PanedWindow(orient=HORIZONTAL)

pw2 = ttk.PanedWindow(orient=VERTICAL)

videoList = Listbox(root, width=50,height=10)
myList = os.listdir(video_dir)
for file in myList:
    videoList.insert(END, file)
videoList.pack()

buttons = Listbox(root)
buttons.pack()


pw4 = ttk.PanedWindow(orient=VERTICAL)

path = Entry(root, textvariable=currentPath)
path.pack(
    fill='x', ipady=5
)

folderUp = Button(root, text='Folder Up', command=goBack)
folderUp.pack(
    fill='x', ipady=2
)
# Keyboard shortcut for going up
root.bind("<Alt-Up>", goBack)



list = Listbox(root)
list.pack(fill=BOTH)

# List Accelerators
list.bind('<Double-1>', changePathByClick)
list.bind('<Return>', changePathByClick)

pw4.add(path)
pw4.add(folderUp)
pw4.add(list)
pw4.pack(fill=BOTH, expand=True)

pw2.add(videoList)
pw2.add(buttons)
pw2.add(pw4)

pw2.pack(fill=BOTH, expand=True )


pw3 = ttk.PanedWindow(orient=VERTICAL)


console = Text(root, font=("consolas", "10", "normal"))
console.pack()
console.tag_config('INFO', background="light green", foreground="blue")
console.tag_config('WARN', background="yellow", foreground="red")


old_stdout = sys.stdout
sys.stdout = StdoutRedirector(console)

old_stderr = sys.stderr
sys.stderr = StdoutRedirector(console)

pb1 = ttk.Progressbar(root, orient=HORIZONTAL, length=100, mode='determinate')
pb1.pack(expand=True)

pw3.add(pb1)
pw3.add(console)
pw3.pack(fill=BOTH, expand=True)

pw.add(pw2)
pw.add(pw3)

pw.pack(fill=BOTH, expand=True)


# open button
open_button = ttk.Button(
    buttons,
    text='Browse',
    command=select_file
)

open_button.pack(side=LEFT, padx=5, pady=5)

delete_button = ttk.Button(
    buttons,
    text='Delete',
    command=deleteItem
)

delete_button.pack(side=LEFT, padx=5, pady=5)


start_button = ttk.Button(
    buttons,
    text='Start',
    command=startRunning
)

start_button.pack(side=RIGHT, padx=5, pady=5)


# Call the function so the list displays
pathChange('')

# run the application
root.mainloop()

sys.stdout = old_stdout
sys.stderr = old_stderr