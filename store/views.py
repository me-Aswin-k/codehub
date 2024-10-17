from django.shortcuts import render,redirect

from django.urls import reverse,reverse_lazy

from django.views.generic import View,TemplateView,UpdateView,CreateView,DetailView,ListView,FormView

from store.forms import SingUpForm,SignInForm,UserProfileForm,ProjectForm,ReviewForm

from django.contrib.auth import authenticate,login,logout

from store.models import UserProfile,Project,WhishListItems,OrderSummary,Reviews

from decouple import config



class SignUpView(View):

    def get(self,requset,*args,**kwargs):

        form_instance=SingUpForm()

        return render(requset,"store/signup.html",{"form":form_instance})

    def post(self,requset,*args,**kwargs):

        form_instance=SingUpForm(requset.POST)

        if form_instance.is_valid():

            form_instance.save()

            return redirect("signin")
        
        return render(requset,"store/signup.html",{"form":form_instance})
    

class SignInView(View):

    def get(self,requset,*args,**kwargs): 

        form_instance=SignInForm()

        return render(requset,"store/login.html",{"form":form_instance})

    def post(self,requset,*args,**kwargs): 
        
        form_instance=SignInForm(requset.POST)

        if form_instance.is_valid():

            data=form_instance.cleaned_data

            user_obj=authenticate(requset,**data)

            if user_obj:

                login(requset,user_obj)

                return redirect("index")
            
        return render(requset,"store/login.html",{"form":form_instance})    





KEY_SECRET=config("KEY_SECRET")

KEY_ID=config("KEY_ID")




class IndexView(View):

    template_name="store/index.html"

    def get(self,requset,*args,**kwargs):

        qs=Project.objects.all().exclude(owner=requset.user)

        return render(requset,self.template_name,{"projects":qs})




class UserProfileUpdateView(UpdateView):

    model=UserProfile

    form_class=UserProfileForm

    template_name="store/profile_edit.html"

    success_url=reverse_lazy("index")

    #def get_success_url(self):

        #return reverse("index")
    

    

    #def get(self,requset,*args,**kwargs):

        #id=kwargs.get("pk")

        #profile_obj=UserProfile.objects.get(id=id)

        #form_instance=UserProfileForm(instance=profile_obj)

        #return render(requset,"store/profile_edit.html",{"form":form_instance})


class ProjectCreateView(CreateView):

    model=Project

    form_class=ProjectForm

    template_name="store/project_add.html"

    success_url=reverse_lazy("index")


    def form_valid(self,form):

        form.instance.owner=self.request.user

        return super().form_valid(form)



#def post(self,request,*args,**kwargs):

#        form_instance=ProjectForm(request.POST,files=request.FILES)

#        if form_instance.is_valid():

#            form_instance.instance.owner=request.user

 #           form_instance.save()

#            return redirect("index")

#        else:

#            return render(request,self.template_name,{"form":form_instance})  



class MyProjectListView(View):

    def get(self,request,*args,**kwargs):

        qs=request.user.projects.all()

        #qs=Project.objects.filter(owner=request.user)

        return render(request,"store/myprojects.html",{"works":qs})



class ProjectDeleteView(View):

    def get(self,request,*args,**kwargs):

        id=kwargs.get("pk")

        Project.objects.get(id=id).delete()

        return redirect("myworks")
    


class ProjectDetailView(DetailView):

    template_name="store/project_detail.html"

    context_object_name="project"

    model=Project




class AddToWishListView(View):

    def get(self,request,*args,**kwargs):

        id=kwargs.get("pk")

        project_obj=Project.objects.get(id=id)

        WhishListItems.objects.create(

            whishlist_object=request.user.basket,

            project_object=project_obj

        )
        print("Item added to WishList")
        
        return redirect("index")


from django.db.models import Sum

class MyCartView(View):

    def get(self,request,*args,**kwargs):

        qs=request.user.basket.basket_items.filter(is_order_placed=False)

        total=request.user.basket.wishlist_total

        return render(request,"store/wishlist_summary.html",{"cartitems":qs,"total":total})
    

class WishListItemDeleteView(View):
   
    def get(self,request,*args,**kwargs):

        id=kwargs.get("pk")

        WhishListItems.objects.get(id=id).delete()

        return redirect("my-cart")



import razorpay

class CheckOutView(View):

    def get(self,request,*args,**kwargs):

        client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))

        amount=request.user.basket.wishlist_total*100

        data = { "amount": amount, "currency": "INR", "receipt": "order_rcptid_11" }

        payment = client.order.create(data=data)

        #oredr_object
        cart_items=request.user.basket.basket_items.filter(is_order_placed=False)

        order_summary_obj=OrderSummary.objects.create(

            user_object=request.user,
            order_id=payment.get("id"),
            total=request.user.basket.wishlist_total
        )

        #order_summary_obj.project_objects.add(cart_items.values("project_object"))

        for ci in cart_items:

            order_summary_obj.project_objects.add(ci.project_object)

            order_summary_obj.save()



        '''for ci in cart_items:
            ci.is_order_placed=True
            ci.save()'''

       


        print(payment)

        context={
            "key":KEY_ID,
            "amount":data.get("amount"),
            "currency":data.get("currency"),
            "order_id":payment.get("id")
        }

        return render(request,"store/payment.html",context)



from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

@method_decorator(csrf_exempt,name="dispatch")
class PaymentVerificationView(View):

    def post(self,request,*args,**kwargs):

        print(request.POST)

        client = razorpay.Client(auth=(KEY_ID, KEY_SECRET))

        order_summary_object=OrderSummary.objects.get(order_id=request.POST.get("razorpay_order_id"))

        login(request,order_summary_object.user_object)

        try:
            client.utility.verify_payment_signature(request.POST)

            print("payment success")

            order_id=request.POST.get("razorpay_order_id")

            OrderSummary.objects.filter(order_id=order_id).update(is_paid=True)

            cart_items=request.user.basket.basket_items.filter(is_oredr_placed=False)

            for ci in cart_items:

                ci.is_order_placed=True
                ci.save()

        except:
            print("payment failed")    

        #return render(request,"store/success.html")
        print(request.user)
        return redirect("index")


class MyPurchaseView(View):    

    model=OrderSummary

    context_object_name="orders"

    def get(self,request,*args,**kwargs):

        qs=OrderSummary.objects.filter(user_object=request.user,is_paid=True)

        return render(request,"store/order_summary.html",{"orders":qs})
    
#localhost:8000/project/<int:pk>/review/add/
class ReviewCreateView(FormView):

    model = Reviews

    template_name="store/review.html"

    form_class=ReviewForm

    def post(self,request,*args,**kwargs):

        id=kwargs.get("pk")

        project_obj=Project.objects.get(id=id)

        form_instance=ReviewForm(request.POST)

        if form_instance.is_valid():

            form_instance.instance.user_object=(request.user)

            form_instance.instance.project_object=project_obj

            form_instance.save()

            return redirect("index")
        else:

            return render(request,self.template_name,{"form":form_instance})









      























    



