#include <stdio.h>
#include <stdlib.h>

int d = 10;
float b = 3.5;
char c = 'A';
int arr[3] = {1, 2, 3};
double e = 3.45454;
// Pointer = address of variable
int a = 10;
int *p = &a;

// *p = 20; // will make a = 20

struct Node {
    int data;
    struct Node* next;
};


int add(int a, int b) {
    return a + b;
}

// Void Function (No return)
void greet() {
    printf("Hello");
}

float divide(int a, int b) {
    return (float)a / b;
}

int main() {
    printf("Hello from VS Code!\n");
    printf("%d\n", d);   // int
    printf("%f\n", b);   // float
    printf("%c\n", c);   // char

    int arr[5] = {1, 2, 3, 4, 5};
    printf("running for arr\n");
    for (int i=0; i<5; i++){
        printf("%d ", arr[i]);
    }
    printf("\n");
    
    // Taking input from an user
    // int x;
    // scanf("%d", &x);
    // if (x>0){
    //     printf("positive \n");
    // } else if (x ==0) {printf("Zero \n");}
    // else {
    //     printf("negative \n");
    // }
for(int i = 0; i < 5; i++) {
    if (i == 3){continue;}
    printf("%d \n", i);
}


    int i = 0;
    while(i < 5) {
        if (i==3){break;}
        printf("%d \n", i);
        i++;
    }


    // do-while Loop 
    int k = 0;
    do {
        printf("%d \n ", i);
        k++;
    } while(k < 5);


    int result = add(3, 4);
    printf("%d \n", result);

    float res1 = divide(4, 2);
    printf("%f \n", res1);
    //  Executes at least once
    return 0;
}


// gcc main.c -o main   # compile
// ./main               # run
