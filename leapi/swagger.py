from leapi import app

@app.route('/leapi-doc/', endpoint='doc')
def swagger_ui():
        return apidoc.ui_for(api)
    
if app.debug:
    @app.route('/swaggerui/bower/<string:path>')
    def send_bower(path):
        return send_from_directory('bower_components', path)
