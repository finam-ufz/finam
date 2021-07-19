# coding=utf-8
# distutils: language=c++

cdef extern from "formind.h":
    cdef cppclass Formind:
        Formind(int seed)
        void initialize()
        void update()
        void finalize()

        double getLai()
        void setSoilMoisture(double sm)
