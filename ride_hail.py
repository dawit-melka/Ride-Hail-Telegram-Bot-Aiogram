import logging, asyncio, sys, os, random, datetime
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.types import ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import CommandStart

from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from dotenv import load_dotenv

from ride_hail_db import insert_passenger_data, insert_driver_data, get_driver_data, get_passenger_data, update_user_data
from ride_hail_db import get_user_by_id, get_all_drivers_id, insert_ride_data, get_passenger_rides, get_driver_rides
from aiogram.handlers.callback_query import CallbackQueryHandler

load_dotenv()

# Initialize Dispatcher and Bot
dp = Dispatcher()
# Create an aiohttp session with the proxy

# session = AiohttpSession(proxy="http://proxy.server:3128")
token = os.getenv("TOKEN2")

bot = Bot(token=token, parse_mode='HTML')

# Registration
class LoginForm(StatesGroup):
    role = State()
    has_account = State()
    isLoggedIn = State()
    email = State()
    password = State()
    register = State()


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
    start = State()
    p_rate = State()
    d_rate = State()

form_router = Router()

@form_router.message(CommandStart())
async def Command_start(message: types.Message, state: FSMContext):
    driver_data = await get_user_by_id("Driver",message.from_user.id)
    passenger_data = await get_user_by_id("Passenger",message.from_user.id)
    if driver_data:
        await state.update_data(role="driver")
        await state.set_state(DriverForm.edit_driver_profile)
        await message.answer(f"Welcome Back {driver_data[1]}!",
                                reply_markup=ReplyKeyboardMarkup(
                                    keyboard=[
                                        [KeyboardButton(text="Manage Profile"),
                                         KeyboardButton(text="Ride History"),]
                                    ],
                                    resize_keyboard=True,
                                ))
    elif passenger_data:
        await state.update_data(role="passenger")
        await state.set_state(PassengerChoice.choice)
        await message.answer(f"Welcome Back {passenger_data[1]}!",
                    reply_markup=ReplyKeyboardMarkup(
                        keyboard=[
                            [
                                KeyboardButton(text="Manage Profile"),
                                KeyboardButton(text="Book Ride")
                            ],
                            [
                                    KeyboardButton(text="Ride History"),
                                ]
                        ],
                        resize_keyboard=True,
                    ))
    else:
        await state.set_state(LoginForm.register)

        await message.answer(
            "Welcome to Ride Hail. Please Register",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [
                        KeyboardButton(text="Register"),
                    ]
                ],
                resize_keyboard=True
            )
        )

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

driver_messages = {}

@form_router.message(Ride.confirm, F.text.casefold() == 'confirm')
async def wait_driver(message: types.Message, state: FSMContext):
    driver_messages.clear()
    await message.answer("Please wait a moment we are looking for a near by driver...", reply_markup=ReplyKeyboardRemove())
    state_data = await state.get_data()
    passenger_data = await get_user_by_id('Passenger', message.from_user.id)
    location = state_data.get('location')
    destination = state_data.get('destination')
    name = f"{passenger_data[1]} {passenger_data[2]}"
    phone = passenger_data[3]
    price = random.randint(150, 500)

    driver_ids = await get_all_drivers_id()
    passenger_info = f"Passenger Name: {name}\nPhone: {phone}\nLocation: {location}\nDestination: {destination}\nPrice: {price}"
    for userId in driver_ids:
        location = "-".join(location.split())
        destination = "-".join(destination.split())
        keyboard = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text='Accept', callback_data=f'{message.from_user.id} {location} {destination} {price}')]])
        sent_message = await bot.send_message(chat_id=userId[0],text=passenger_info, reply_markup=keyboard)

        # Store the message ID for each driver
        driver_messages[userId[0]] = sent_message.message_id
    await state.set_state(Ride.d_rate)


@form_router.callback_query()
async def accept_ride(q: types.CallbackQuery, state: FSMContext):
    driver_data = await get_user_by_id("Driver", q.from_user.id)
    name = f"{driver_data[1]} {driver_data[2]}"
    phone = driver_data[3]
    car_type = driver_data[6]
    plate_no = driver_data[7]
    print(q.data)
    p_id, location, destination, price = q.data.split()
    await state.update_data(passenger_id = p_id)
    await state.update_data(location = location)
    await state.update_data(destination = destination)
    await state.update_data(price = price)
    await bot.send_message(chat_id=q.data, text=f"Your ride has been accepted by {name}\nPhone: {phone}\nCar Type: {car_type}\nPlate Number: {plate_no}", reply_markup=None)
    # Remove the inline keyboards for all drivers
    print(driver_messages)
    for driver_id, message_id in driver_messages.items():
        if driver_id == q.from_user.id:
            await bot.edit_message_reply_markup(chat_id=driver_id, message_id=message_id, reply_markup=None)
        else:
            await bot.delete_message(chat_id=driver_id, message_id=message_id)
    await state.set_state(Ride.start)
    await q.message.answer("Press the button below to start the ride.",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[
                                 [
                                     KeyboardButton(text="Start Ride")
                                 ]
                             ],
                             resize_keyboard=True,
                         ))

@form_router.message(Ride.start)
async def start_ride(message: types.Message, state: FSMContext):
    await state.set_state(Ride.complete)
    await message.answer("Ride started. Press the button below to complete the ride.",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[
                                 [
                                     KeyboardButton(text="Complete")
                                 ]
                             ],
                             resize_keyboard=True,
                         ))
    data = await state.get_data()
    passenger_id = data.get('passenger_id')
    await bot.send_message(chat_id=passenger_id, text="Your trip has started. Enjoy the ride!")

@form_router.message(Ride.complete)
async def complete_ride(message: types.Message, state: FSMContext):
    await state.set_state(Ride.p_rate)
    data = await state.get_data()
    driver_id = message.from_user.id
    passenger_id = data.get('passenger_id')
    location = " ".join(data.get('location').split("-"))
    destination = " ".join(data.get('destination').split("-"))
    distance = random.randint(5, 15)
    time = random.randint(10, 30)
    price = data.get('price')
    date = datetime.datetime.now().strftime("%d-%b-%Y")
    await insert_ride_data(driver_id, passenger_id, location, destination, distance, time, price, date)

    await message.answer(f"Ride Completed!\nFrom {location} To {destination}\nDuration: {time} min\nDistance: {distance} km\nPrice: {price} ETB\n\n Please Rate the Passenger",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[
                                 [
                                     KeyboardButton(text="1"),
                                     KeyboardButton(text="2"),
                                     KeyboardButton(text="3"),
                                     KeyboardButton(text="4"),
                                     KeyboardButton(text="5"),
                                 ]
                             ],
                             resize_keyboard=True,
                         ))
    await bot.send_message(chat_id=passenger_id, text=f"Ride Completed!\nFrom {location} To {destination}\nDuration: {time} min\nDistance: {distance} km\nPrice: {price} ETB\n\n Please Rate the Driver",
                           reply_markup=ReplyKeyboardMarkup(
                             keyboard=[
                                 [
                                     KeyboardButton(text="1"),
                                     KeyboardButton(text="2"),
                                     KeyboardButton(text="3"),
                                     KeyboardButton(text="4"),
                                     KeyboardButton(text="5"),
                                 ]
                             ],
                             resize_keyboard=True,
                         ))

@form_router.message(Ride.p_rate, lambda message: message.text in ["1", "2", "3", "4", "5"])
async def rate_passenger(message: types.Message, state: FSMContext):
    await state.set_state(DriverForm.edit_driver_profile)
    await message.answer("Thank you for using Ride Hail!",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[
                                 [
                                     KeyboardButton(text="Manage Profile"),
                                     KeyboardButton(text="Ride History"),
                                 ]
                             ],
                             resize_keyboard=True
                         ))
@form_router.message(Ride.d_rate, lambda message: message.text in ["1", "2", "3", "4", "5"])
async def rate_passenger(message: types.Message, state: FSMContext):
    await state.set_state(PassengerChoice.choice)
    await message.answer("Thank you for using Ride Hail!",
                         reply_markup=ReplyKeyboardMarkup(
                             keyboard=[
                                 [
                                     KeyboardButton(text="Manage Profile"),
                                     KeyboardButton(text="Book Ride")
                                 ],
                                [
                                     KeyboardButton(text="Ride History"),
                                 ]
                             ],
                             resize_keyboard=True
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

@form_router.message(PassengerChoice.choice, F.text.casefold() == "ride history")
async def passenger_ride_history(message: types.Message, state: FSMContext):
    rides = await get_passenger_rides(message.from_user.id)
    ride_history = ""
    if len(rides) == 0:
        ride_history = "No ride history!"

    for ride in rides:
        driver = await get_user_by_id("Driver", ride[1])
        print(driver)
        print(ride[1])
        driver_name = f"{driver[1]} {driver[2]}"
        ride_info = f"Driver: {driver_name}\nDate: {ride[8]}\nPick up: {ride[3]}\nDrop off: {ride[4]}\nPrice: {ride[7]}\n\n"
        ride_history += ride_info
    await state.set_state(PassengerChoice.choice)
    await message.answer(f"Ride History\n{ride_history}", reply_markup=ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Manage Profile"),
             KeyboardButton(text="Book Ride")
             ],
            [KeyboardButton(text="Ride History")]
        ],
        resize_keyboard=True
    ))

@form_router.message(PassengerChoice.what_to_edit, lambda message: message.text in ["first_name", "last_name", "phone", "email", "password"])
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
    new_data = await update_user_data('Passenger', message.from_user.id, data.get('what_to_edit'), new_val)

    await message.answer(f"You have successfully updated your {data.get('what_to_edit')} \n {new_data}",
                         reply_markup=ReplyKeyboardMarkup(
                            keyboard=[
                                [
                                    KeyboardButton(text="Manage Profile"),
                                    KeyboardButton(text="Book Ride")
                                ],
                                [
                                     KeyboardButton(text="Ride History"),
                                 ]
                            ],
                            resize_keyboard=True,
                        ))



@form_router.message(DriverForm.edit_driver_profile, F.text.casefold() == "manage profile")
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

@form_router.message(DriverForm.edit_driver_profile, F.text.casefold() == "ride history")
async def driver_ride_history(message: types.Message, state: FSMContext):
    rides = await get_driver_rides(message.from_user.id)
    ride_history = ""
    if len(rides) == 0:
        ride_history = "No ride history!"
    total = 0
    for ride in rides:
        passenger = await get_user_by_id("Passenger", ride[2])
        passenger_name = f"{passenger[1]} {passenger[2]}"
        ride_info = f"Passenger: {passenger_name}\nDate: {ride[8]}\nPick up: {ride[3]}\nDrop off: {ride[4]}\nPrice: {ride[7]}\n\n"
        ride_history += ride_info
        total += int(ride[7])
    await state.set_state(DriverForm.edit_driver_profile)
    await message.answer(f"<b><u>RIDE HISTORY</u></b>\n\n{ride_history}<b>Total: {total} ETB</b>",

                         reply_markup=ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Manage Profile"),
            KeyboardButton(text="Ride History")]
        ],
        resize_keyboard=True
    ))

@form_router.message(DriverForm.what_to_edit, lambda message: message.text in ["first_name", "last_name", "phone", "email", "password"])
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
    new_data = await update_user_data('Driver', message.from_user.id, data.get('what_to_edit'), new_val)

    await message.answer(f"You have successfully updated your {data.get('what_to_edit')} \n {new_data}",
                         reply_markup=ReplyKeyboardMarkup(
                            keyboard=[
                                [
                                    KeyboardButton(text="Manage Profile"),
                                    KeyboardButton(text="Ride History"),
                                ]
                            ],
                            resize_keyboard=True,
                        ))

@form_router.message(LoginForm.register)
async def process_registration(message: types.Message, state: FSMContext):

    await state.update_data(has_account="no")
    await state.set_state(RegisterForm.role)
    await message.answer("Please answer the following questions to register!\nAre you Passenger or Driver?",
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
                        reply_markup=ReplyKeyboardMarkup(
                            keyboard=[
                                [
                                    KeyboardButton(text="Share Phone number", request_contact=True),
                                ]
                            ]
                        ))

@form_router.message(RegisterForm.phone)
async def register_email(message: types.Message, state: FSMContext):
    await state.update_data(phone=message.contact.phone_number)
    await state.set_state(RegisterForm.email)
    await message.answer("Please send your email",
                        reply_markup=ReplyKeyboardRemove())

@form_router.message(RegisterForm.email)
async def register_password(message: types.Message, state: FSMContext):
    await state.update_data(email=message.text)
    await state.set_state(RegisterForm.password)
    await message.answer("Please send your password",
                        reply_markup=ReplyKeyboardRemove())

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
                                    ],
                                [
                                     KeyboardButton(text="Ride History"),
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
                                        KeyboardButton(text="Ride History")
                                    ]
                                ],
                                resize_keyboard=True,
                            ))
@form_router.message()
async def unknown_command(message: types.Message):
    await message.answer("Sorry, I didn't understand that. Let's start start again.\nPress the button below to start.",
                         reply_markup=ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="/start"),
            ]
        ],
        resize_keyboard=True
    ))

async def main():
    dp.include_router(form_router)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
