#include "formind.h"
#include <iostream>
#include <random>

Formind::Formind(int seed) {
    time = 0;
    soil_moisture = 0.0;
    lai = 0.0;

    eng.seed(seed);
    distr = std::uniform_real_distribution<float>(0.5, 1.0);
}

Formind::~Formind() {}

void Formind::initialize() {}

void Formind::update() {
    double growth = (1.0 - exp(-0.1 * soil_moisture)) * distr(eng);
    lai = (lai + growth) * 0.9;

    time += 1;
}

void Formind::finalize() {}

double Formind::getLai() {
    return lai;
}

void Formind::setSoilMoisture(double sm) {
    soil_moisture = sm;
}
