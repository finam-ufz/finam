#include "formind.h"
#include <iostream>

Formind::Formind() {
    time = 0;
    std::cout << "Creating model" << std::endl;
}

Formind::~Formind() {
    std::cout << "Destructing model" << std::endl;
}

void Formind::initialize() {
    std::cout << "Initializing model" << std::endl;
}

void Formind::update() {
    std::cout << "  Updating model: " << time << std::endl;
    time += 1;
}

void Formind::finalize() {
    std::cout << "Finalizing model" << std::endl;
    time += 1;
}
