from tkinter import *
from tkinter import messagebox
import requests
import configparser
import xmltodict
import pprint

# configurations ##############################################################
config = configparser.ConfigParser()
config.read('config.ini')

apikey = config['misc']['apikey']
set_id = config['misc']['set_id']

# main program ################################################################
def main(*args):
    # barcode
    barcode = gui.get_barcode()
    if barcode == "":
        gui.msgbox(barcode, "Bad barcode.")
        return
    gui.clear_barcode()
    
    # get item record
    r = requests.get(f"https://api-na.hosted.exlibrisgroup.com/almaws/v1/items?item_barcode={barcode}&apikey={apikey}")
    
    # check for errors
    errors_exist = check_errors(r)
    if errors_exist[0] == True:
        error = errors_exist[1]
        gui.msgbox(barcode, error)
        return
    
    # parse item record
    item_xml   = r.text
    item_dict  = xmltodict.parse(r.text, dict_constructor=dict) 
    title      = item_dict['item']['bib_data']['title']
    mms_id     = item_dict['item']['bib_data']['mms_id']
    holding_id = item_dict['item']['holding_data']['holding_id']
    item_pid   = item_dict['item']['item_data']['pid']

    # add to set
    set_xml = generateSetXML(set_id, mms_id, holding_id, item_pid, barcode)
    r = postXML(f"https://api-na.hosted.exlibrisgroup.com/almaws/v1/conf/sets/{set_id}?op=add_members&apikey={apikey}", set_xml)
    
    # check for errors
    errors_exist = check_errors(r)
    if errors_exist[0] == True:
        error = errors_exist[1]
        gui.msgbox(title, error)
        return
        
    # finish
    gui.update_status_success(title[:60])
            
# functions ###################################################################
def postXML(url, xml):
    headers = {'Content-Type': 'application/xml', 'charset':'UTF-8'}
    r = requests.post(url, data=xml.encode('utf-8'), headers=headers)
    return r

def generateSetXML(set_id, mms_id, holding_id, item_id, barcode):
    set_xml = \
f"""<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<set link="https://api-na.hosted.exlibrisgroup.com/almaws/v1/conf/sets/{set_id}">
  <id>{set_id}</id>
  <number_of_members link="https://api-na.hosted.exlibrisgroup.com/almaws/v1/conf/sets/{set_id}/members">1</number_of_members>
<members total_record_count="1">
  <member link="https://api-na.hosted.exlibrisgroup.com/almaws/v1/bibs/{mms_id}/holdings/{holding_id}/items/{item_id}">
    <id>{item_id}</id>
    <description>{barcode}</description>
  </member>
</members>
</set>"""

    return set_xml
    
def check_errors(r):
    if r.status_code != 200:
        errors = xmltodict.parse(r.text)
        error = errors['web_service_result']['errorList']['error']['errorMessage']
        return True, error
    else: 
        return False, "OK"
            
# gui #########################################################################
class gui:
    def __init__(self, master):
        self.master = master
        master.title("LazyLists 2.4")
        master.resizable(0, 0)
        master.minsize(width=600, height=100)
        master.iconbitmap("logo_small.ico")

        logo = PhotoImage(file="logo_large.png")
        self.logo = Label(image=logo)
        self.logo.image = logo
        self.logo.pack()

        self.status_title = Label(height=1, text="Scan barcode to begin.", font="Consolas 12 italic")
        self.status_title.pack(fill="both", side="top")

        self.status_added = Label(height=1, text="READY", font="Consolas 12 bold", fg="green")
        self.status_added.pack(fill="both", side="top")

        self.barcode_entry_field = Entry(font="Consolas 16")
        self.barcode_entry_field.focus()
        self.barcode_entry_field.bind('<Key-Return>', main)
        self.barcode_entry_field.pack(fill="both", side="top")
        
        self.scan_button = Button(text="SCAN", font="Arial 16", command=main)
        self.scan_button.pack(fill="both", side="top")
        
    def msgbox(self, title, msg):
        messagebox.showerror("Attention", msg)
        gui.update_status_failure(title, msg)
        
    def get_barcode(self):
        barcode = self.barcode_entry_field.get()
        barcode = barcode.replace(" ", "")
        return barcode
        
    def clear_barcode(self):
        self.barcode_entry_field.delete(0, END)
        self.status_title.config(text="")
        self.status_added.config(text="")
        
    def update_status_success(self, title):
        self.status_title.config(text=title)
        self.status_added.config(text="SUCCESSFULLY ADDED TO SET", fg="green")
        
    def update_status_failure(self, title, msg):
        self.status_title.config(text=title)
        self.status_added.config(text=msg, fg="red")
        
root = Tk()
gui = gui(root)
root.mainloop()