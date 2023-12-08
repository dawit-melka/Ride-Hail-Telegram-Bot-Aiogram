import logging, asyncio, sys, os
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types.callback_query import CallbackQuery
from dotenv import load_dotenv

from ride_hail_db import insert_passenger_data, insert_driver_data, get_driver_data, get_passenger_data, update_user_data, get_user_by_id, get_all_drivers_id

load_dotenv()

# Initialize Dispatcher and Bot
dp = Dispatcher()
# Create an aiohttp session with the proxy

# session = AiohttpSession(proxy="http://proxy.server:3128")
token = os.getenv("TOKEN2")
# token = "6852134606:AAFiyI-UHrIow3qPq08_SF1tYUylPkT-Lgg"
bot = Bot(token=token, parse_mode='HTML')

# Registration
class LoginForm(StatesGroup):
    role = State()
    has_account = State()
    isLoggedIn = State()
    email = State()
    password = State()


class RegisterForm(StatesGroup):
    first_name = State()
    last_name = State()
    phone = State()
    role = State()
    email = State()
    password = State()

class PassengerChoice(StatesGroup):
    choice = State()
    what_to_edit = State()
    edit_data = State()
    
class DriverForm(StatesGroup):
    plate_number = State()
    car_type = State()
    edit_driver_profile = State()
    what_to_edit = State()
    edit_data = State()

class Ride(StatesGroup):
    location = State()
    destination = State()
    confirm = State()
    complete = State()
    

form_router = Router()

@form_router.message(CommandStart())
async def Command_start(message: types.Message, state: FSMContext):
    await state.set_state(LoginForm.has_account)
    
    await message.answer(
        "Welcome! Do you have account?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [
                    KeyboardButton(text="Yes"),
                    KeyboardButton(text="No")
                ]
            ],
            resize_keyboard=True,
        )
    )

# Process has_account
@form_router.message(LoginForm.has_account, F.text.casefold() == "yes")
async def process_accept_role(message: types.Message, state: FSMContext):
    await state.update_data(has_account="yes")
    await state.set_state(LoginForm.role)
    
    # await bot.send_message(chat_id=message.from_user.id, text='heyyyy davo', request_timeout=20000,reply_markup=ReplyKeyboardRemove())
    await message.answer(f"Are you Passenger or Driver?",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[
                                 [
                                     KeyboardButton(text="Passenger"),
                                     KeyboardButton(text="Driver")
                                 ]
                             ],
                             
                         resize_keyboard=True,
                         )
                         )
    
@form_router.message(LoginForm.role, F.text.casefold() == "passenger")
async def process_passenger_login_email(message: types.Message, state: FSMContext):
    await state.update_data(role="passenger")
    await state.set_state(LoginForm.email)
    await message.answer("Please send your email to login",
                        reply_markup=ReplyKeyboardRemove())


@form_router.message(LoginForm.role, F.text.casefold() == "driver")
async def process_driver_login_email(message: types.Message, state: FSMContext):
    await state.update_data(role="driver")
    await state.set_state(LoginForm.email)
    await message.answer("Please send your email to login",
                        reply_markup=ReplyKeyboardRemove())

@form_router.message(LoginForm.email)
async def process_login_password(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    await state.set_state(LoginForm.password)
    await message.answer("Please send your password",
                        reply_markup=ReplyKeyboardRemove())

@form_router.message(LoginForm.password)
async def authenticate_user(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)
    # await state.set_state(LoginForm.isLoggedIn)
    data = await state.get_data()
    role = data.get("role")
    email = data.get("email")
    password = data.get("password")
    
    # check from the database and authenticate
    
    await state.update_data(isLoggedIn=True)
    if role == 'passenger':
        user_data = await get_passenger_data(email,password)
    else:
        user_data = await get_driver_data(email,password)
    
    if user_data != None:
        await state.update_data(userId = user_data[0])
        if role == "passenger":
            await state.set_state(PassengerChoice.choice)
            await message.answer(f"You have successfully logged in{user_data}",
                        reply_markup=ReplyKeyboardMarkup(
                            keyboard=[
                                [
                                    KeyboardButton(text="Manage Profile"),
                                    KeyboardButton(text="Book Ride")
                                ]
                            ],
                            resize_keyboard=True,
                        ))
        else:
            await state.set_state(DriverForm.edit_driver_profile)
            await message.answer(f"You have successfully logged in {user_data}",
                                 reply_markup=ReplyKeyboardMarkup(
                                     keyboard=[
                                         [KeyboardButton(text="Edit Profile")]
                                     ],
                                     resize_keyboard=True,
                                 ))
    else:
        await state.set_state(LoginForm.email)
        await message.answer(f"Wrong email or password \nPlease enter your email again. ",
                        reply_markup=ReplyKeyboardRemove())

@form_router.message(PassengerChoice.choice, F.text.casefold() == "book ride")
async def book_ride_location(message: types.Message, state: FSMContext):
    await state.set_state(Ride.location)
    await message.answer("Please send your location", 
                         reply_markup=ReplyKeyboardRemove())

@form_router.message(Ride.location)
async def book_ride_destination(message: types.Message, state: FSMContext):
    await state.update_data(location=message.text)
    await state.set_state(Ride.destination)
    await message.answer("Please send your destination", 
                         reply_markup=ReplyKeyboardRemove())
    
@form_router.message(Ride.destination)
async def confirm_ride(message: types.Message, state: FSMContext):
    await state.update_data(destination=message.text)
    await state.set_state(Ride.confirm)
    data = await state.get_data()
    location = data.get('location')
    destination = data.get('destination')
    await message.answer(f"Please confirm your ride. \nLocation: {location}\nDestination: {destination}",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[
                                 [
                                     KeyboardButton(text="Confirm"),
                                     KeyboardButton(text="Cancel")
                                 ]
                             ],
                             resize_keyboard=True
                         ))

@form_router.message(Ride.confirm, F.text.casefold() == 'confirm')
async def wait_driver(message: types.Message, state: FSMContext):
    await message.answer("Please wait a moment we are looking for a near by driver...", reply_markup=ReplyKeyboardRemove())
    await asyncio.sleep(5)
    driver_ids = await get_all_drivers_id()
    print(driver_ids)
    for userId in driver_ids:
        await bot.send_message(chat_id=userId[0], text="Pease accept this ride", reply_markup=ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text='Accept Ride')]]))
        
    await message.answer("Driver on the way!\nSilver Toyota Vitz\nB31698\nAhmed Gashu")
    await asyncio.sleep(5)
    await state.set_state(Ride.complete)
    await message.answer("Driver arived. Have a good trip :)", reply_markup=ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text='Complete Ride')
            ]
        ],
        resize_keyboard=True
    ))


@form_router.message(Ride.complete)
async def complete_ride(message: types.Message, state: FSMContext):
    
    await state.set_state(PassengerChoice.choice)
    await message.answer("Thankyou for using Ride Hail! \nDuration: 19m 15s\nDistance: 8 km\nPrice: 250",
                         reply_markup=ReplyKeyboardMarkup(
                            keyboard=[
                                [
                                    KeyboardButton(text="Manage Profile"),
                                    KeyboardButton(text="Book Ride")
                                ]
                            ],
                            resize_keyboard=True,
                        ))
    
@form_router.message(PassengerChoice.choice, F.text.casefold() == "manage profile")
async def manage_passenger_profile(message: types.Message, state: FSMContext):
    await state.set_state(PassengerChoice.what_to_edit)
    await message.answer("What do you want to edit?", reply_markup=ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='first_name'), KeyboardButton(text='last_name')],
            [KeyboardButton(text='phone'), KeyboardButton(text='email')], 
            [KeyboardButton(text='password')],
        ],
        resize_keyboard=True,
        input_field_placeholder='Select one',
    ))

@form_router.message(PassengerChoice.what_to_edit)
async def edit_passenger_data(message: types.Message, state: FSMContext):
    await state.update_data(what_to_edit = message.text)
    await state.set_state(PassengerChoice.edit_data)
    data = await state.get_data()
    await message.answer(f"Please send new {data.get('what_to_edit')}", 
                         reply_markup=ReplyKeyboardRemove())
    
@form_router.message(PassengerChoice.edit_data)
async def process_edit_passenger_data(message: types.Message, state: FSMContext):
    new_val = message.text
    await state.set_state(PassengerChoice.choice)
    data = await state.get_data()
    new_data = await update_user_data(data.get('role'), data.get('userId'), data.get('what_to_edit'), new_val)
    
    await message.answer(f"You have successfully updated your {data.get('what_to_edit')} \n {new_data}", 
                         reply_markup=ReplyKeyboardMarkup(
                            keyboard=[
                                [
                                    KeyboardButton(text="Manage Profile"),
                                    KeyboardButton(text="Book Ride")
                                ]
                            ],
                            resize_keyboard=True,
                        ))


    
@form_router.message(DriverForm.edit_driver_profile)
async def manage_driver_profile(message: types.Message, state: FSMContext):
    await state.set_state(DriverForm.what_to_edit)
    await message.answer("What do you want to edit?", reply_markup=ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text='first_name'), KeyboardButton(text='last_name')],
            [KeyboardButton(text='phone'), KeyboardButton(text='email')], 
            [KeyboardButton(text='password')],
        ],
        resize_keyboard=True,
    ))

@form_router.message(DriverForm.what_to_edit)
async def edit_driver_data(message: types.Message, state: FSMContext):
    await state.update_data(what_to_edit = message.text)
    await state.set_state(DriverForm.edit_data)
    data = await state.get_data()
    await message.answer(f"Please send new {data.get('what_to_edit')}", 
                         reply_markup=ReplyKeyboardRemove())
    
@form_router.message(DriverForm.edit_data)
async def process_edit_driver_data(message: types.Message, state: FSMContext):
    new_val = message.text
    await state.set_state(DriverForm.edit_driver_profile)
    data = await state.get_data()
    new_data = await update_user_data(data.get('role'), data.get('userId'), data.get('what_to_edit'), new_val)
    
    await message.answer(f"You have successfully updated your {data.get('what_to_edit')} \n {new_data}", 
                         reply_markup=ReplyKeyboardMarkup(
                            keyboard=[
                                [
                                    KeyboardButton(text="Edit Profile")
                                ]
                            ],
                            resize_keyboard=True,
                        ))

@form_router.message(LoginForm.has_account, F.text.casefold() == "no")
async def process_registration(message: types.Message, state: FSMContext):
    
    await state.update_data(has_account="no")
    await state.set_state(RegisterForm.role)
    await message.answer("Okay wellcome please answer the following questions to register!\nAre you Passenger or Driver?",
                            reply_markup=ReplyKeyboardMarkup(
                                keyboard=[
                                    [
                                        KeyboardButton(text="Passenger"),
                                        KeyboardButton(text="Driver")
                                    ]
                                ],
                                resize_keyboard=True,
                            ))

    
@form_router.message(RegisterForm.role, F.text.casefold() == "driver")
async def process_driver_register_first_name(message: types.Message, state: FSMContext):
    await state.update_data(role="driver")
    user_id = message.from_user.id
    prev_acc = await get_user_by_id("Driver", user_id)
    if prev_acc == None:
        await state.set_state(RegisterForm.first_name)
        await message.answer("What is your first name?",
                            reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer(f"You already have an account{prev_acc}", reply_markup=ReplyKeyboardRemove())


@form_router.message(RegisterForm.role, F.text.casefold() == "passenger")
async def process_passenger_register_first_name(message: types.Message, state: FSMContext):
    await state.update_data(role="passenger")
    user_id = message.from_user.id
    prev_acc = await get_user_by_id("Passenger", user_id)
    if prev_acc == None:
        await state.set_state(RegisterForm.first_name)
        await message.answer("What is your first name?",
                            reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer(f"You already have an account{prev_acc}",reply_markup=ReplyKeyboardRemove())

@form_router.message(RegisterForm.first_name)
async def register_last_name(message: types.Message, state: FSMContext):
    await state.update_data(first_name=message.text)
    await state.set_state(RegisterForm.last_name)
    await message.answer("Please send your last name",
                        reply_markup=ReplyKeyboardRemove())

@form_router.message(RegisterForm.last_name)
async def register_phone_number(message: types.Message, state: FSMContext):
    await state.update_data(last_name=message.text)
    await state.set_state(RegisterForm.phone)
    await message.answer("Please send your phone number",
                        reply_markup=ReplyKeyboardRemove())

@form_router.message(RegisterForm.phone)
async def register_email(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.text)
    await state.set_state(RegisterForm.email)
    await message.answer("Please send your email",
                        reply_markup=ReplyKeyboardRemove())

@form_router.message(RegisterForm.email)
async def register_password(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    await state.set_state(RegisterForm.password)
    await message.answer("Please send your password",
                        reply_markup=ReplyKeyboardRemove())

'''
@form_router.message(LoginForm.has_account, F.text.casefold() == "no")
@form_router.message(LoginForm.password)
async def register_confirm_password(message: types.Message, state: FSMContext):
    # await state.update_data(password=message.text)
    # await state.set_state(LoginForm.confirm_password)
    # await message.answer("Please confirm your password",
    #                      reply_markup=ReplyKeyboardRemove())
    pass
'''
@form_router.message(RegisterForm.password)
async def process_passenger_registration(message: types.Message, state: FSMContext):
    await state.update_data(password=message.text)
    data = await state.get_data()
    isPassenger = data.get('role') == 'passenger'
    if isPassenger:
        userId = message.from_user.id
        first_name = data.get('first_name') 
        last_name = data.get('last_name')
        phone = data.get('phone')
        email = data.get('email')
        password = data.get('password')
        

        await insert_passenger_data(userId, first_name, last_name, phone, email, password)
        await state.set_state(PassengerChoice.choice)
        user_data = await get_passenger_data(email, password)
        await state.update_data(userId=user_data[0])
        await message.answer(f"You have successfully registered{user_data}",
                        reply_markup=ReplyKeyboardMarkup(
                                keyboard=[
                                    [
                                        KeyboardButton(text="Manage Profile"),
                                        KeyboardButton(text="Book Ride")
                                    ]
                                ],
                                resize_keyboard=True,
                            ))

    else:
        await state.set_state(DriverForm.car_type)
        await message.answer("What is your car color and model?", reply_markup=ReplyKeyboardRemove())
        
@form_router.message(DriverForm.car_type)
async def regiser_car(message: types.Message, state: FSMContext):
    await state.update_data(car_type = message.text)
    await state.set_state(DriverForm.plate_number)
    await message.answer("What is your car plate number?", reply_markup=ReplyKeyboardRemove())

   
   
@form_router.message(DriverForm.plate_number)
async def process_driver_registration(message: types.Message, state: FSMContext):
    await state.update_data(plate_number=message.text)
    data = await state.get_data()
    userId = message.from_user.id
    first_name = data.get('first_name') 
    last_name = data.get('last_name')
    phone = data.get('phone')
    email = data.get('email')
    password = data.get('password')
    car_type = data.get('car_type')
    plate_no = data.get('plate_number')
    await insert_driver_data(userId, first_name, last_name, phone, email, password, car_type, plate_no)
    await state.update_data(isLoggedIn=True)
    await state.set_state(DriverForm.edit_driver_profile)
    user_data = await get_driver_data(email, password)
    await state.update_data(userId=user_data[0])
    await message.answer(f"You have successfully registerd{data}", 
                         reply_markup=ReplyKeyboardMarkup(
                                keyboard=[
                                    [
                                        KeyboardButton(text="Manage Profile"),
                                    ]
                                ],
                                resize_keyboard=True,
                            )) 
    
# Book Ride



async def main():
    dp.include_router(form_router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
