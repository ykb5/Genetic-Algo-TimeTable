from django.shortcuts import render, redirect
from .models import *
import random as rnd
from. forms import *

from django.contrib.auth.forms import  AuthenticationForm
from django.contrib.auth import login,logout
from django.contrib.auth.decorators import login_required

POPULATION_SIZE = 9
NUMB_OF_ELITE_SCHEDULES = 1
TOURNAMENT_SELECTION_SIZE = 3
MUTATION_RATE = 0.1
#collects the data inserted using frontend components, uses models.py file
class Data:
    def __init__(self):
        self._rooms = Room.objects.all()
        self._meetingTimes = MeetingTime.objects.all()
        self._instructors = Instructor.objects.all()
        self._courses = Course.objects.all()
        self._depts = Department.objects.all()

    def get_rooms(self): return self._rooms

    def get_instructors(self): return self._instructors

    def get_courses(self): return self._courses

    def get_depts(self): return self._depts

    def get_meetingTimes(self): return self._meetingTimes

#generates a schedule
class Schedule:
    def __init__(self):
        self._data = data
        self._classes = []
        self._numberOfConflicts = 0
        self._fitness = -1
        self._classNumb = 0
        self._isFitnessChanged = True

    def get_classes(self):
        self._isFitnessChanged = True
        return self._classes

    def get_numbOfConflicts(self): return self._numberOfConflicts

    def get_fitness(self):
        if self._isFitnessChanged:
            self._fitness = self.calculate_fitness()
            self._isFitnessChanged = False
        return self._fitness

    #This method create classes for all the sections by allocating rooms, instructors and meeting times randomly.
    # def initialize(self):
    #     sections = Section.objects.all()
    #     for section in sections:
    #         dept = section.department
    #         n = section.num_class_in_week
    #         if n <= len(MeetingTime.objects.all()):
    #             courses = dept.courses.all()
    #             for course in courses:
    #                 for i in range(n // len(courses)):
    #                     crs_inst = course.instructors.all()
    #                     newClass = Class(self._classNumb, dept, section.section_id, course)
    #                     self._classNumb += 1
    #                     newClass.set_meetingTime(data.get_meetingTimes()[rnd.randrange(0, len(MeetingTime.objects.all()))])
    #                     newClass.set_room(data.get_rooms()[rnd.randrange(0, len(data.get_rooms()))])
    #                     newClass.set_instructor(crs_inst[rnd.randrange(0, len(crs_inst))])
    #                     self._classes.append(newClass)
    #         else:
    #             n = len(MeetingTime.objects.all())
    #             courses = dept.courses.all()
    #             for course in courses:
    #                 for i in range(n // len(courses)):
    #                     crs_inst = course.instructors.all()
    #                     newClass = Class(self._classNumb, dept, section.section_id, course)
    #                     self._classNumb += 1
    #                     newClass.set_meetingTime(data.get_meetingTimes()[rnd.randrange(0, len(MeetingTime.objects.all()))])
    #                     newClass.set_room(data.get_rooms()[rnd.randrange(0, len(data.get_rooms()))])
    #                     newClass.set_instructor(crs_inst[rnd.randrange(0, len(crs_inst))])
    #                     self._classes.append(newClass)

    #     return self

    # Initialization
    def initialize(self):
        sections = Section.objects.all()
        meeting_times = list(MeetingTime.objects.all())
        rooms = data.get_rooms()

        for section in sections:
            dept = section.department
            courses = dept.courses.all()
            num_classes_per_week = section.num_class_in_week #18
            n = min(num_classes_per_week, len(meeting_times))

            for course in courses:
                crs_inst = course.instructors.all()
                for i in range(n // len(courses)):
                    new_class = Class(self._classNumb, dept, section.section_id, course)
                    self._classNumb += 1
                    new_class.set_meetingTime(meeting_times[rnd.randrange(len(meeting_times))])
                    new_class.set_room(rooms[rnd.randrange(len(rooms))])
                    new_class.set_instructor(crs_inst[rnd.randrange(len(crs_inst))])
                    self._classes.append(new_class)
        return self
    #This function calculates scheduled class fitness based on number of conflicts.
    def calculate_fitness(self):
        self._numberOfConflicts = 0
        classes = self.get_classes()
        for i in range(len(classes)):
            #if room capacity < maximum number of students in course, this is conflict.
            if classes[i].room.seating_capacity < int(classes[i].course.max_numb_students):
                self._numberOfConflicts += 1
            for j in range(len(classes)):
                if j >= i:
                    #for a same section, having different section_id (different classes schedules) at same time , it is conflict.
                    if (classes[i].meeting_time == classes[j].meeting_time) and (classes[i].section_id != classes[j].section_id) and (classes[i].section == classes[j].section):
                        if classes[i].room == classes[j].room:
                            self._numberOfConflicts += 1
                        if classes[i].instructor == classes[j].instructor:
                            self._numberOfConflicts += 1
        return 1 / (1.0 * self._numberOfConflicts + 1)

#A population consist of  all the schedules generated here equal to POPULATION_SIZE in a generation.
class Population:
    def __init__(self, size):
        self._size = size
        self._data = data
        self._schedules = [Schedule().initialize() for i in range(size)]

    def get_schedules(self):
        return self._schedules

data = Data()
class GeneticAlgorithm:
    def evolve(self, population):#schedules in a population is sorted based on their fitness values.
        return self._mutate_population(self._crossover_population(population))

    def _crossover_population(self, pop):
        crossover_pop = Population(0)
        for i in range(NUMB_OF_ELITE_SCHEDULES):#first schedule i.e. fittest schedule is chosen.
            crossover_pop.get_schedules().append(pop.get_schedules()[i])
        i = NUMB_OF_ELITE_SCHEDULES

        while i < POPULATION_SIZE:
            #Choosing two schedules, applying crossover over them and storing the result in crossover_pop
            schedule1 = self._select_tournament_population(pop).get_schedules()[0]
            schedule2 = self._select_tournament_population(pop).get_schedules()[0]
            crossover_pop.get_schedules().append(self._crossover_schedule(schedule1, schedule2))
            i += 1
        return crossover_pop

    def _mutate_population(self, population):
        for i in range(NUMB_OF_ELITE_SCHEDULES, POPULATION_SIZE):
            self._mutate_schedule(population.get_schedules()[i])
        return population

    def _crossover_schedule(self, schedule1, schedule2):
        crossoverSchedule = Schedule().initialize()
        for i in range(0, len(crossoverSchedule.get_classes())):
            if rnd.random() > 0.5:
                crossoverSchedule.get_classes()[i] = schedule1.get_classes()[i]
            else:
                crossoverSchedule.get_classes()[i] = schedule2.get_classes()[i]
        return crossoverSchedule

    def _mutate_schedule(self, mutateSchedule):
        schedule = Schedule().initialize()
        for i in range(len(mutateSchedule.get_classes())):
            if MUTATION_RATE > rnd.random():
                mutateSchedule.get_classes()[i] = schedule.get_classes()[i]
        return mutateSchedule

    def _select_tournament_population(self, pop):
        tournament_pop = Population(0)
        i = 0
        while i < TOURNAMENT_SELECTION_SIZE:
            tournament_pop.get_schedules().append(pop.get_schedules()[rnd.randrange(0, POPULATION_SIZE)])
            i += 1
        tournament_pop.get_schedules().sort(key=lambda x: x.get_fitness(), reverse=True)
        return tournament_pop

#It is an entity of a schedule
class Class:
    def __init__(self, id, dept, section, course):
        self.section_id = id
        self.department = dept
        self.course = course
        self.instructor = None
        self.meeting_time = None
        self.room = None
        self.section = section

    def get_id(self): return self.section_id

    def get_dept(self): return self.department

    def get_course(self): return self.course

    def get_instructor(self): return self.instructor

    def get_meetingTime(self): return self.meeting_time

    def get_room(self): return self.room

    def set_instructor(self, instructor): self.instructor = instructor

    def set_meetingTime(self, meetingTime): self.meeting_time = meetingTime

    def set_room(self, room): self.room = room


# data = Data()


def context_manager(schedule):
    classes = schedule.get_classes()
    context = []
    cls = {}
    for i in range(len(classes)):
        cls["section"] = classes[i].section_id
        cls['dept'] = classes[i].department.dept_name
        cls['course'] = f'{classes[i].course.course_name} ({classes[i].course.course_number}, ' \
                        f'{classes[i].course.max_numb_students}'
        cls['room'] = f'{classes[i].room.r_number} ({classes[i].room.seating_capacity})'
        cls['instructor'] = f'{classes[i].instructor.name} ({classes[i].instructor.uid})'
        cls['meeting_time'] = [classes[i].meeting_time.pid, classes[i].meeting_time.day, classes[i].meeting_time.time]
        context.append(cls)
    return context


#login
def login_view(request):
    if request.user.is_authenticated:  # Check if the user is already authenticated
        return redirect('mm1:home')  # Redirect to home page if already logged in
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request,user)
            if 'next' in request.POST:
                return redirect(request.POST.get('next'))
            else:
                return redirect('mm1:home')
    else:
        form = AuthenticationForm()
    return render(request,'login.html',{'form':form})


#logout
def logout_view(request):
    if(request.method == 'POST'):
        logout(request)
        return redirect('mm1:login')



#This method calls the methods get_schedules() to create schedules for a population and call geneticAlgorithm() method.

def timetable(request):
    schedule = []
    population = Population(POPULATION_SIZE) #initialization call
    generation_num = 0
    population.get_schedules().sort(key=lambda x: x.get_fitness(), reverse=True)#schedules are sorted in decreasing number of fitness values.
    geneticAlgorithm = GeneticAlgorithm()
    count =1
    while population.get_schedules()[0].get_fitness() != 1.0:#Loop untill we get fitness = 1
        generation_num += 1
        print('\n> Generation #' + str(generation_num))
        population = geneticAlgorithm.evolve(population) #Evolution call
        population.get_schedules().sort(key=lambda x: x.get_fitness(), reverse=True)
        schedule = population.get_schedules()[0].get_classes()
        count += 1
    return render(request, 'timetable.html', {'schedule': schedule, 'sections': Section.objects.all(),
                                              'times': MeetingTime.objects.all()})

@login_required(login_url='mm1:login')
def home(request):
    return render(request, 'index.html', {})

@login_required(login_url='mm1:login')
def add_instructor(request):
    form = InstructorForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('mm1:addinstructor')
    context = {
        'form': form
    }
    return render(request, 'adins.html', context)


def inst_list_view(request):
    context = {
        'instructors': Instructor.objects.all()
    }
    return render(request, 'instlist.html', context)

def delete_instructor(request, pk):
    inst = Instructor.objects.filter(pk=pk)
    if request.method == 'POST':
        inst.delete()
        return redirect('mm1:editinstructor')

@login_required(login_url='mm1:login')
def add_room(request):
    form = RoomForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('mm1:addroom')
    context = {
        'form': form
    }
    return render(request, 'addrm.html', context)

def room_list(request):
    context = {
        'rooms': Room.objects.all()
    }
    return render(request, 'rmlist.html', context)

def delete_room(request, pk):
    rm = Room.objects.filter(pk=pk)
    if request.method == 'POST':
        rm.delete()
        return redirect('mm1:editrooms')

def meeting_list_view(request):
    context = {
        'meeting_times': MeetingTime.objects.all()
    }
    return render(request, 'mtlist.html', context)

@login_required(login_url='mm1:login')
def add_meeting_time(request):
    form = MeetingTimeForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('mm1:addmeetingtime')
        else:
            print('Invalid')
    context = {
        'form': form
    }
    return render(request, 'addmt.html', context)

def delete_meeting_time(request, pk):
    mt = MeetingTime.objects.filter(pk=pk)
    if request.method == 'POST':
        mt.delete()
        return redirect('mm1:editmeetingtime')


def course_list_view(request):
    context = {
        'courses': Course.objects.all()
    }
    return render(request, 'crslist.html', context)

@login_required(login_url='mm1:login')
def add_course(request):
    form = CourseForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('mm1:addcourse')
        else:
            print('Invalid')
    context = {
        'form': form
    }
    return render(request, 'adcrs.html', context)


def delete_course(request, pk):
    crs = Course.objects.filter(pk=pk)
    if request.method == 'POST':
        crs.delete()
        return redirect('editcourse')

@login_required(login_url='mm1:login')
def add_department(request):
    form = DepartmentForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('mm1:adddepartment')
    context = {
        'form': form
    }
    return render(request, 'addep.html', context)


def department_list(request):
    context = {
        'departments': Department.objects.all()
    }
    return render(request, 'deptlist.html', context)


def delete_department(request, pk):
    dept = Department.objects.filter(pk=pk)
    if request.method == 'POST':
        dept.delete()
        return redirect('mm1:editdepartment')

@login_required(login_url='mm1:login')
def add_section(request):
    form = SectionForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            form.save()
            return redirect('mm1:addsection')
    context = {
        'form': form
    }
    return render(request, 'addsec.html', context)


def section_list(request):
    context = {
        'sections': Section.objects.all()
    }
    return render(request, 'seclist.html', context)


def delete_section(request, pk):
    sec = Section.objects.filter(pk=pk)
    if request.method == 'POST':
        sec.delete()
        return redirect('mm1:editsection')
