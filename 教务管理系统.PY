class student:
    def __init__(self,name,chinese,math,english):
        self.name=name
        self.chinese=chinese
        self.math=math
        self.english=english
    def xiu(self,chinese=None,math=None,english=None):
        if chinese !=None:
            self.chinese=chinese
        if math !=None:
            self.math=math
        if english!=None:
            self.english=english

    def __str__(self):
        return f"姓名:{self.name},语文成绩:{self.chinese},数学成绩:{self.math},英语成绩:{self.english}"
class edu:
    edu_version=1.0
    def __init__(self):
        self.stulist=[]

    def addstu(self):
        name=input("请输入名字")
        for i in self.stulist:
            if name==i.name:
                print("该学生已存在")
                return
        chinese=int(input("请输入语文成绩"))
        math=int(input("请输入数学成绩"))
        english=int(input("请输入英语成绩"))
        stu=student(name,chinese,math,english)
        self.stulist.append(stu)

        

    def fixstu(self):
        name=input("输入要修改的学生姓名")
        for i in self.stulist:
            if name==i.name:
                chinese=int(input("请输入语文成绩"))
                math=int(input("请输入数学成绩"))
                english=int(input("请输入英语成绩")) 
                i.xiu(chinese,math,english)
                print("成绩修改完成:",i)
                return
        print("未找到该学生")

    def delstu(self):
        name=input("输入要删除的学生姓名")
        for i in self.stulist:
            if name==i.name:
                self.stulist.remove(i)
                print("删除成功")    
                return
        print("未找到该学生")

    def searchstu(self):
        name=input("输入要查询的学生姓名")
        for i in self.stulist:
            if name==i.name:
                print(i)    
            return
        print("未找到该学生")    
    def lookalstu(self):
        for i in self.stulist:
            print(i)            
jiaowu=edu()
                
print("欢迎来到教务管理系统")
while True:
    print('''
    ###################
    1.添加学生成绩     
    2.修改学生成绩     
    3.删除学生成绩     
    4.查询指定学生成绩 
    5.展示全部学生成绩
    6.退出
    #################
    ''')
    a=input()
    match a:
        case "1":
            jiaowu.addstu()
            uiu=input()
        case "2":
            jiaowu.fixstu()
            uiu=input()
        case "3":
            jiaowu.delstu()
            uiu=input()
        case "4":
            jiaowu.searchstu()
            uiu=input()
        case "5":
            jiaowu.lookalstu()
            uiu=input()
        case "6":
            break