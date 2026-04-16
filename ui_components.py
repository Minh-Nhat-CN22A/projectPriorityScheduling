# ui_components.py - UI Components
import customtkinter as ctk

def create_input_row(parent, row_index, delete_callback):
    """Create an input row with a Delete button"""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.grid(row=row_index, column=0, sticky="ew", pady=2)
    
    label = ctk.CTkLabel(frame, text=f"P{row_index}", width=40)
    label.pack(side="left", padx=5)
    
    arr = ctk.CTkEntry(frame, placeholder_text="Arrival", width=80)
    arr.pack(side="left", padx=5)
    
    bst = ctk.CTkEntry(frame, placeholder_text="Burst", width=80)
    bst.pack(side="left", padx=5)
    
    pri = ctk.CTkEntry(frame, placeholder_text="Priority", width=80)
    pri.pack(side="left", padx=5)
    
    btn_del = ctk.CTkButton(frame, text="X", width=30, fg_color="red", 
                            command=lambda: delete_callback(frame))
    btn_del.pack(side="left", padx=5)
    
    return {"frame": frame, "arrival": arr, "burst": bst, "priority": pri}