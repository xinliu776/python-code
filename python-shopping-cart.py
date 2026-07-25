# 第二次练习git
class goods:
    def __init__(self,name,price,count):
        self.name=name
        self.price=price
        self.count=count

    def __str__(self):
        return f"商品名称:{self.name},商品价格:{self.price},商品数量:{self.count}"

    def xiu(self,price=None,count=None):
        if price is not None:
            self.price=price
        if count is not None:    
            self.count=count

class sys:
    def __init__(self):
        self.goodlist=[]

    def add(self):
        name=input("请输入商品名称")
        for i in self.goodlist:
            if i.name==name:
                print("商品已存在")
                return
        price=int(input("请输入商品价格"))
        count=int(input("请输入商品数量"))
        good=goods(name,price,count)
        self.goodlist.append(good)
        print("添加成功")

    def fix(self):
        name=input("请输入要修改的商品名称")
        for i in self.goodlist:
            if i.name==name:
                price=int(input("请输入价格"))    
                count=int(input("请输入数量"))
                i.xiu(price,count)
                
                return
        print("未找到该商品")

    def delg(self):
        name=input("请输入要删除的商品名称")
        for i in self.goodlist:
            if i.name==name:
                self.goodlist.remove(i)
                return
        print("未找到该商品")

    def look(self):
        for i in self.goodlist:
            print(i)

print("欢迎来到购物系统")
sys1=sys()
while True:
    print('''
#################################################
1.添加商品 2.修改商品 3.删除商品 4.查看购物车 5.退出
#################################################
''')
    a=input()
    match a:
        case "1":
            sys1.add()
            x=input()
        case "2":
            sys1.fix()
            x=input()
        case "3":
            sys1.delg()
            x=input()
        case "4":
            sys1.look()
            x=input()
        case "5":
            break
        
        