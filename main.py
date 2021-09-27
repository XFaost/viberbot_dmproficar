from flask import Flask, request, Response
from flask_sqlalchemy import SQLAlchemy
from viberbot import Api
from viberbot.api.bot_configuration import BotConfiguration
from viberbot.api.messages import VideoMessage
from viberbot.api.messages.text_message import TextMessage
from viberbot.api.viber_requests import ViberConversationStartedRequest
from viberbot.api.viber_requests import ViberFailedRequest
from viberbot.api.viber_requests import ViberMessageRequest
from viberbot.api.viber_requests import ViberSubscribedRequest
from viberbot.api.viber_requests import ViberUnsubscribedRequest
import socket
from decouple import config


ip_server = socket.gethostbyname(socket.gethostname())

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)



def get_or_create(session, model, **kwargs):
    instance = session.query(model).filter_by(**kwargs).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        session.commit()
        return instance

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    viber_id = db.Column(db.String(50), nullable=False)
    
    def __repr__(self):
        return '<User %r>' % self.viber_id
        
db.create_all()

viber = Api(BotConfiguration(
    name = 'DM PROFICAR',
    avatar = 'http://dmproficar.com/static/logo/black_bg.webp',
    auth_token = config('VIBER_AUTH_TOKEN')
))


def distribution_client(values):

    name = values.get('name')
    phone = values.get('phone')
    car_name = values.get('car_name')
    
    text_mess = ""
    
    if(car_name):
        text_mess += car_name + '\n\n'
    text_mess += f"Ім`я: {name}\nНомер: {phone}"

    users = User.query.all()
    for user in users:    
        viber.send_messages(user.viber_id, [
            TextMessage(text=text_mess)
        ])


@app.route('/', methods=['GET'])
def get():
    data = request.get_data()    
    
    return Response(f"<h1>hello</h1><p>{str(data)}</p>")

@app.route('/', methods=['POST'])
def incoming():

    if request.remote_addr == ip_server:
        values = request.values
        distribution_client(values)
        return Response(status=200)

    if not viber.verify_signature(request.get_data(), request.headers.get('X-Viber-Content-Signature')):
        return Response(status=403)

    viber_request = viber.parse_request(request.get_data())
    
    
    
    
    

    if isinstance(viber_request, ViberMessageRequest):
        message = viber_request.message
        user_id = viber_request.sender.id
        
        if message.text == "Підписатися":            

            if not User.query.filter_by(viber_id=user_id).first():
                user = User(viber_id=user_id)
                db.session.add(user)
                db.session.commit()
                
                viber.send_messages(user_id, [
                    TextMessage(text=f"Ви підписані на розсилку!")
                ])
            else:
                viber.send_messages(user_id, [
                    TextMessage(text=f"Ви вже підписані!")
                ])
          
            
    elif isinstance(viber_request, ViberSubscribedRequest):
        pass
    elif isinstance(viber_request, ViberUnsubscribedRequest):
        User.query.filter_by(viber_id=viber_request.user_id).delete()
        db.session.commit()
        
    elif isinstance(viber_request, ViberConversationStartedRequest):
        pass
     

    return Response(status=200)





if __name__ == "__main__":    
    app.run(host="0.0.0.0", debug=True) 
    
