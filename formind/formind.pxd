# coding=utf-8
# distutils: language=c++

cdef extern from "formind.h":
    cdef cppclass Formind:
        Formind()
        void initialize()
        void update()
        void finalize()
