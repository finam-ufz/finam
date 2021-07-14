cdef class Model():
    
    cdef Formind *formind
    
    def __cinit__(self, int seed):
        self.formind = new Formind(seed)

    def __dealloc__(self):
        del self.formind
        self.formind = NULL

    def initialize(self):
        self.formind.initialize()
 
    def update(self):
        self.formind.update()

    def finalize(self):
        self.formind.finalize()

    def getLai(self):
        return self.formind.getLai();

    def setSoilMoisture(self, double sm):
        self.formind.setSoilMoisture(sm);
