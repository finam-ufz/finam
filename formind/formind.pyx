cdef class Model():
    
    cdef Formind *formind
    
    def __cinit__(self, int seed):
        self.formind = new Formind(seed)
    
    def __dealloc__(self):
        if self.formind is not NULL:
            del self.formind
            self.formind = NULL
       
    def initialize(self):
        self.formind[0].initialize()
 
    def update(self):
        self.formind[0].update()

    def finalize(self):
        self.formind[0].finalize()
