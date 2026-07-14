#include <stdio.h>

#define MAX 100

// Heap size
int size = 0;

// Function to swap two elements
void swap(int *a, int *b) {
    int temp = *a;
    *a = *b;
    *b = temp;
}

// Heapify DOWN (used in delete)
void heapify(int heap[], int i) {
    int largest = i;
    int left = 2*i + 1;
    int right = 2*i + 2;

    if (left < size && heap[left] > heap[largest])
        largest = left;

    if (right < size && heap[right] > heap[largest])
        largest = right;

    if (largest != i) {
        swap(&heap[i], &heap[largest]);
        heapify(heap, largest);
    }
}

// Insert into Max Heap
void insert(int heap[], int value) {
    int i = size;
    heap[i] = value;
    size++;

    // Heapify UP
    while (i != 0 && heap[(i - 1) / 2] < heap[i]) {
        swap(&heap[i], &heap[(i - 1) / 2]);
        i = (i - 1) / 2;
    }
}

// Delete root (maximum element)
void deleteMax(int heap[]) {
    if (size == 0) {
        printf("Heap is empty\n");
        return;
    }

    printf("Deleted element: %d\n", heap[0]);

    heap[0] = heap[size - 1];
    size--;

    heapify(heap, 0);
}

// Display heap elements
void display(int heap[]) {
    if (size == 0) {
        printf("Heap is empty\n");
        return;
    }

    printf("Heap elements: ");
    for (int i = 0; i < size; i++)
        printf("%d ", heap[i]);
    printf("\n");
}

// Main function
int main() {
    int heap[MAX];
    int choice, value;

    while (1) {
        printf("\n--- MAX HEAP MENU ---\n");
        printf("1. Insert\n");
        printf("2. Delete Max\n");
        printf("3. Display\n");
        printf("4. Exit\n");
        printf("Enter choice: ");
        scanf("%d", &choice);

        switch (choice) {
            case 1:
                printf("Enter value: ");
                scanf("%d", &value);
                insert(heap, value);
                break;

            case 2:
                deleteMax(heap);
                break;

            case 3:
                display(heap);
                break;

            case 4:
                return 0;

            default:
                printf("Invalid choice\n");
        }
    }
}
