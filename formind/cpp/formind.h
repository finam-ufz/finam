#ifndef FORMIND_H
#define FORMIND_H

#include <random>

class Formind {
    private:
        int time;
        double soil_moisture;
        double lai;

        std::default_random_engine eng;
        std::uniform_real_distribution<float> distr;

    public:
        Formind(int seed);
        ~Formind();

        void initialize();
        void update();
        void finalize();
};

#endif
