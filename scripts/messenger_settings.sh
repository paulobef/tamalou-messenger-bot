#!/bin/bash

if [ -f ".env" ]; 
then
    # Load Environment Variables
    ACCESS_TOKEN=$(grep ACCESS_TOKEN= .env | cut -d '=' -f2)
    
    # Set Get Started
    curl -X POST -H "Content-Type: application/json" -d '{
      "get_started": {"payload": "START"},
    }' "https://graph.facebook.com/v7.0/me/messenger_profile?access_token=$ACCESS_TOKEN"
    
    # Set Greetings
    curl -X POST -H "Content-Type: application/json" -d '{
      "greeting":[
        {
          "locale":"default",
          "text":"Salut {{user_first_name}} ! Bienvenue sur Tamalou, ton compagnon dans les bons et les mauvais moments. Clique sur Démarrer pour commencer la discussion."
        }
      ]
    }' "https://graph.facebook.com/v7.0/me/messenger_profile?access_token=$ACCESS_TOKEN"
    
    # Set Persistent Menu
    curl -X POST -H "Content-Type: application/json" -d '{
      "persistent_menu": [
        {
            "locale": "default",
            "composer_input_disabled": false,
            "call_to_actions": [
                {
                    "type": "postback",
                    "title": "Nouvelle conversation",
                    "payload": "RESTART"
                },
                {
                    "type": "postback",
                    "title": "Plus d'\''explications",
                    "payload": "EXPLAIN"
                },
            ]
        }
      ]
    }' "https://graph.facebook.com/v7.0/me/messenger_profile?access_token=$ACCESS_TOKEN" 
else
  echo "no env file at indicated location"  
fi

