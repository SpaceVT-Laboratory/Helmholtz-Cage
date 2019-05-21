/*
Control Code for Aduino - Determines the on/off of the relays 
 */

// the setup routine runs once when you press reset:
void setup() 
{
  int i;
  for(i = 8; i < 14; i++){
    pinMode(i, OUTPUT);
  }
  // initialize serial communication at 9600 bits per second:
  Serial.begin(9600);
  digitalWrite(9, HIGH);
  digitalWrite(8, HIGH);
  digitalWrite(11, HIGH);
  digitalWrite(10, HIGH);
  digitalWrite(13, HIGH);
  digitalWrite(12, HIGH);
 }

 void loop(){
  char command = Serial.read();
  if(command == 'f'){
    digitalWrite(9, LOW);
    digitalWrite(8, HIGH);}
  else if(command == 'g'){ 
    digitalWrite(8, LOW);
    digitalWrite(9, HIGH);} 
  else if(command == 'h'){
    digitalWrite(11, LOW);
    digitalWrite(10, HIGH);}
  else if(command == 'i'){ 
    digitalWrite(10, LOW);
    digitalWrite(11, HIGH);} 
  else if(command == 'j'){
    digitalWrite(13, LOW);
    digitalWrite(12, HIGH);}
  else if(command == 'k'){ 
    digitalWrite(12, LOW);
    digitalWrite(13, HIGH);} 
  else if(command == 'l'){
    digitalWrite(13, HIGH);
    digitalWrite(12, HIGH);
    digitalWrite(11, HIGH);
    digitalWrite(10, HIGH);
    digitalWrite(9, HIGH);
    digitalWrite(8, HIGH);}
  }


