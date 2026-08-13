#!/bin/bash

echo "What programming language do you learn"
echo "1. Python"
echo "2. JavaScript"

read -n 1 -p "Make your choice (1 or 2): " choice

if [ "$choice" == "1" ]; then
  echo "Great Choice! Python is a great language"
elif [ "$choice" == "2" ]; then
  echo "Also not bad, You will create the websites"
else
  echo "Incorrect choice"
fi