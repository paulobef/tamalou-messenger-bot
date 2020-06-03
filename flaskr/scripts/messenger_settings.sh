
#!/bin/bash
curl -X POST -H "Content-Type: application/json" -d '{
  "get_started": {"payload": "Démarrer"}
}' "https://graph.facebook.com/v2.6/me/messenger_profile?access_token=EAAJjz4uEYEUBAPnrPhECxc9NIlT9Kmqup8F8RZCHuqMzh0qr0wiHptGqvnXbOuozd56Bn5vyjh59ckIuRwgQsxuhQzZAhybuYl9IvBwYhlFfDY730TE2vIvyRSv27W7BvkNZARm3epYA8adVQohsLf1ZBHiBlbyxh7oGANFHFgZDZD"