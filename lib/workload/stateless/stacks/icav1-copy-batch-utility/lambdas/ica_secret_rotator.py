import libica.app.libgds

def handler(event, context):
    print(libica.app.libgds.get_folder_cred("gds://production"))