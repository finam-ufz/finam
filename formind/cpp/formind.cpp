#include "formind.h"
#include <iostream>
#include <random>

Formind::Formind(int seed) {
    std::cout << "Creating model with seed " << seed << std::endl;

    time = 0;
    soil_moisture = 0.0;
    lai = 0.0;

    eng.seed(seed);
    distr = std::uniform_real_distribution<float>(0.5, 1.0);
}

Formind::~Formind() {
    std::cout << "Destructing model" << std::endl;
}

void Formind::initialize() {
    std::cout << "Initializing model" << std::endl;
}

void Formind::update() {
    std::cout << "  Updating model: " << time << std::endl;

    double growth = (1.0 - exp(-0.1 * soil_moisture)) * distr(eng);
    lai = (lai + growth) * 0.9;

    time += 1;
}

void Formind::finalize() {
    std::cout << "Finalizing model" << std::endl;
}
