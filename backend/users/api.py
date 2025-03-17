from ninja import Router, Schema
from django.contrib import auth
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from django import forms
from django.http import HttpResponseBadRequest
from django.shortcuts import get_list_or_404, get_object_or_404

from django.contrib.auth.models import User
from ninja import ModelSchema
from typing import List

router = Router()

class Error(Schema):
    message: str

class UserSchema(ModelSchema):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']


class RegisterForm(forms.Form):
    username = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Email have exists.')
        return username

class RegisterIn(Schema):
    username: str
    password: str

@router.post('/register', auth=None)
def register(request, payload: RegisterIn):
    formData = {
        'username': payload.username,
        'password': payload.password
    }

    form = RegisterForm(formData)
    if form.is_valid():
        user = User.objects.create_user(
            username=payload.username,
            password=payload.password,
            email=payload.username
        )
        return {"message": "create user success!"}
    else:
        return HttpResponseBadRequest(form.errors.as_json())


@router.get('/', response=List[UserSchema])
def user_list(request):
    """Get user list"""
    if request.auth:
        curuser = request.auth
        print(curuser)
    else:
        return HttpResponseBadRequest('Not found user.')
    users = get_list_or_404(User)
    return list(users)

@router.get('/info', response=UserSchema)
def user_info(request):
    user = User.objects.filter(username=request.auth).first()
    return user

@router.post('/{userid}/reset')
def reset_default_password(request, userid: int):
    if request.auth:
        curuser = request.auth
        print(curuser)
    else:
        return HttpResponseBadRequest('Not found user.')
    user = get_object_or_404(User, id=userid)
    user.set_password("abc123456")
    user.save()
    return {"detail": "success"}


class UpdateIn(Schema):
    password: str

@router.post('/{userid}/update')
def update_password(request, userid: int, payload: UpdateIn):
    if request.auth:
        curuser = request.auth
        print(curuser)
    else:
        return HttpResponseBadRequest('Not found user.')
    if curuser.id != userid:
        return HttpResponseBadRequest('Current user is not login user.')
    user = get_object_or_404(User, id=userid)
    user.set_password(payload.password)
    user.save()
    return {"detail": "success"}
