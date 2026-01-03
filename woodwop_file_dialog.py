"""
WoodWOP Custom File Dialog Module
This module provides a beautiful, modern file save dialog specifically for MPR files.
It handles different PySide versions and ensures .mpr extension is always used.
"""

import os

# Try to import Qt modules (handle different versions)
QtWidgets = None
QtGui = None
QFileDialog = None
QMessageBox = None

def _import_qt_modules():
    """Import Qt modules, trying different versions."""
    global QtWidgets, QtGui, QFileDialog, QMessageBox
    
    if QFileDialog is not None:
        return True
    
    # Try PySide6 first (newest)
    try:
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        from PySide6 import QtGui, QtWidgets
        return True
    except ImportError:
        pass
    
    # Try PySide2 (common)
    try:
        from PySide2.QtWidgets import QFileDialog, QMessageBox
        from PySide2 import QtGui, QtWidgets
        return True
    except ImportError:
        pass
    
    # Try old PySide (QtGui.QFileDialog)
    try:
        from PySide.QtGui import QFileDialog, QMessageBox
        import PySide.QtGui as QtGui
        QtWidgets = QtGui
        return True
    except ImportError:
        pass
    
    return False


def show_save_dialog(parent=None, default_filename="", default_directory=""):
    """
    Show a beautiful file save dialog for MPR files.
    
    Args:
        parent: Parent widget (optional)
        default_filename: Default filename (without extension)
        default_directory: Default directory path
        
    Returns:
        str: Selected file path with .mpr extension, or None if cancelled
    """
    if not _import_qt_modules():
        # Fallback to standard file dialog if Qt is not available
        return None
    
    # Ensure default filename has .mpr extension
    if default_filename:
        base_name, ext = os.path.splitext(default_filename)
        if ext.lower() != '.mpr':
            default_filename = base_name + '.mpr'
    else:
        default_filename = "output.mpr"
    
    # Set default directory
    if not default_directory:
        default_directory = os.path.expanduser("~")
    
    # Create beautiful file dialog
    dialog = QFileDialog(parent)
    
    # Set dialog properties for save mode
    dialog.setFileMode(QFileDialog.FileMode.AnyFile)
    dialog.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
    dialog.setDirectory(default_directory)
    
    # Set default filename
    dialog.selectFile(default_filename)
    
    # Set filter for MPR files (beautiful and clear)
    dialog.setNameFilter("WoodWOP MPR Files (*.mpr);;All Files (*)")
    dialog.setDefaultSuffix("mpr")  # Automatically add .mpr if user doesn't specify
    
    # Set beautiful window title
    dialog.setWindowTitle("💾 Save WoodWOP MPR File")
    
    # Set label text (if available in this Qt version)
    try:
        # Try new Qt6/PySide6 style
        dialog.setLabelText(QFileDialog.DialogLabel.Accept, "💾 Save")
        dialog.setLabelText(QFileDialog.DialogLabel.Reject, "❌ Cancel")
    except (AttributeError, TypeError):
        try:
            # Try Qt5/PySide2 style
            dialog.setLabelText(QFileDialog.Accept, "💾 Save")
            dialog.setLabelText(QFileDialog.Reject, "❌ Cancel")
        except (AttributeError, TypeError):
            # Older Qt versions - labels not available
            pass
    
    # Try to set options for better appearance (if available)
    try:
        # Use native dialog if available (looks better on macOS/Windows)
        dialog.setOption(QFileDialog.Option.DontUseNativeDialog, False)
    except (AttributeError, TypeError):
        try:
            dialog.setOption(QFileDialog.DontUseNativeDialog, False)
        except (AttributeError, TypeError):
            pass
    
    # Show dialog and get result
    if dialog.exec_():
        selected_files = dialog.selectedFiles()
        if selected_files:
            filepath = selected_files[0]
            
            # CRITICAL: Ensure .mpr extension
            base_name, ext = os.path.splitext(filepath)
            if ext.lower() != '.mpr':
                filepath = base_name + '.mpr'
            
            return filepath
    
    return None  # User cancelled


def show_info_message(parent=None, title="Information", message=""):
    """
    Show a beautiful information message box.
    
    Args:
        parent: Parent widget (optional)
        title: Message box title
        message: Message text
        
    Returns:
        bool: True if user clicked OK
    """
    if not _import_qt_modules():
        return False
    
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Information)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    
    return msg_box.exec_() == QMessageBox.StandardButton.Ok


def show_warning_message(parent=None, title="Warning", message=""):
    """
    Show a beautiful warning message box.
    
    Args:
        parent: Parent widget (optional)
        title: Message box title
        message: Message text
        
    Returns:
        bool: True if user clicked OK
    """
    if not _import_qt_modules():
        return False
    
    msg_box = QMessageBox(parent)
    msg_box.setIcon(QMessageBox.Icon.Warning)
    msg_box.setWindowTitle(title)
    msg_box.setText(message)
    msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
    
    return msg_box.exec_() == QMessageBox.StandardButton.Ok

