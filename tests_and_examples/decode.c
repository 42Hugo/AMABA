unsigned int counter = 0;
unsigned int blink = 0;
unsigned int dig1=0;
unsigned int dig2=0;
unsigned int dig3=0;
float ana1=0.0f;
float ana2=0.0f;
unsigned int state= 1;


void decodeMessage(const char *mes)
{
    state=mes[0]-'0';
    dig1=mes[1]-'0';
    dig2=mes[2]-'0';
    dig3=mes[3]-'0';
    if (mes[4] - '0'!=0){
        ana1 = (mes[4] - '0') * 10 + (mes[5] - '0');
        ana1 = (ana1 / 20.0f) * 65535.0f;//on the 0-2 bar VPPM
    }
    else if (mes[5] - '0'!=0){
        ana1 = (mes[5] - '0');
        ana1 = (ana1 / 20.0f) * 65535.0f;//on the 0-2 bar VPPM
    }
    else{
        ana1=0;
    }

    if (mes[6] - '0'!=0){
        ana2 = (mes[6] - '0') * 10 + (mes[7] - '0');
        ana2 = (ana2 / 20.0f) * 21845.0f;//on the 0-6 bar vppm final approximation will have to be defined
    }
    else if (mes[7] - '0'!=0){
        ana2 = (mes[7] - '0');
        ana2 = (ana2 / 20.0f) * 21845.0f;//on the 0-6 bar VPPM
    }
    else{
        ana2=0;
    }
}

int main (){
    char text[]="10012000";
    decodeMessage(text);
    printf("Analog Output 1: %.2f\n", ana1);
    printf("Analog Output 2: %.2f\n", ana2);
    printf("State: %u\n", state);

    return 0;
}