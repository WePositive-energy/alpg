
    #Copyright (C) 2023 University of Twente

    #This program is free software: you can redistribute it and/or modify
    #it under the terms of the GNU General Public License as published by
    #the Free Software Foundation, either version 3 of the License, or
    #(at your option) any later version.

    #This program is distributed in the hope that it will be useful,
    #but WITHOUT ANY WARRANTY; without even the implied warranty of
    #MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    #GNU General Public License for more details.

    #You should have received a copy of the GNU General Public License
    #along with this program.  If not, see <http://www.gnu.org/licenses/>.


# Within this file, models to generate heat-specific profile and data are provided.
# Think of domestic hot water (DHW) usage, thermostat setpoints, heat generated by users

# Heat demand of households is taken out of the generation as this demand depends on the runtimes of the heating devices
# such as a heat pump or CHP. Instead we provide flexibility information that can be loaded in a thermal zone model.
# based on the flexibility, the modelled zone, and the heating device, (optimizing) controllers can be implemented in the external too
# such as DEMKit to simulate the temperature behaviour of the zone based on the control actions.

from alpg.configLoader import config
import random

# HeatDevice is the overall class for these devices
class HeatDevice:
	def __init__(self, consumption = 0):
		self.generate(consumption)
		
	def generate(self, consumption = 0):
		self.State = 0
		self.Consumption = consumption
		
	def writeDevice(self, hnum):
		pass


# DHW Profile generation based on the occupancy and daily schedule
class DHWDemand(HeatDevice):
	def __init__(self, consumption = 0):
		self.generate(consumption)

	def generate(self, consumption = 0):
		pass

	def simulate(self, persons, occupancyPerson, dayOfWeek, cookingTime = None, cookingDuration = None, hasDishwasher = None):
		powerPerLitre = (4186 * (60-20)) /60.0
		# Note: Power consumption for a litre using the specific heat and assuming a temperature difference of ~40 times 60 as we use minutes

		result = [0] * 1440
		showerOccupancy = [0] * 1440

		cookingIncluded = False
		if cookingDuration == 0:
			cookingIncluded = True

		for p in range(0, len(persons)):
			pResult = [0] * 1440

			showerStart = None
			showerDuration = 0
			rand = random.randint(0, 100)
			if (dayOfWeek in persons[p].showerDays or rand < 15) and not rand >= 85:
				showerDuration = random.randint(persons[p].showerDuration-1, persons[p].showerDuration+1)

			if showerDuration > 0: #actually use the shower
				# First obtain a shower profile for this person
				showerOptions = []
				for i in range(0, 1440 - (showerDuration+5)):
					option = True
					if showerOccupancy[i] == 0 and occupancyPerson[p][i] > 0 and occupancyPerson[p][i+showerDuration+5] > 0 and showerOccupancy[i+showerDuration+5] == 0:
						# Check for sure:
						for j in range(i, i+showerDuration+5):
							if showerOccupancy[j] != 0 or occupancyPerson[p][j] == 0:
								option = False
								break
							if cookingIncluded == False and j >= cookingTime and j <= (cookingTime+cookingDuration):
								option = False
								break
						if option:
							showerOptions.append(i)

				# Now determine when to shower exactly:
				if persons[p].showerMorning and len(showerOptions) > 0:
					# Try to get the earliest possible moment
					showerStart = showerOptions[0]
				elif len(showerOptions) > 0:
					# Most likely in the evening, after dinner, so >=  19 o clock:
					tries = 0
					while tries < 10:
						showerStart = random.sample(showerOptions, 1)[0]
						if showerStart > 19*60:
							break
						tries += 1

				# Now really add the shower:
				if showerStart != None:
					for i in range(showerStart, showerStart+showerDuration):
						pResult[i] = 0.083 * powerPerLitre * 60

					for i in range(showerStart, showerStart+showerDuration+5):
						showerOccupancy[i] = 1

			# Determine DHW usage for cooking (First person only):
			if cookingIncluded == False:
				# select some random moments during cooking:
				cookingmoments = range(cookingTime, cookingTime+cookingDuration)
				tapUsage = random.sample(cookingmoments, random.randint(1, 4))
				for i in tapUsage:
					pResult[i] = 0.083 * powerPerLitre * rand.randInt(30, 60)

				# Now check for dishes or precleaning
				if not hasDishwasher or random.randint(0,10) < 4:
					dishmoment = cookingTime + cookingDuration + random.randint(30,45)
					if occupancyPerson[p][dishmoment] > 0:
						pResult[dishmoment] = 0.083 * powerPerLitre * 60
					if occupancyPerson[p][dishmoment+1] > 0:
						pResult[dishmoment] = 0.083 * powerPerLitre * 60

				cookingIncluded = True

			# Now determine normal hot water usage
			options = []
			# First fill a list with appropriate moments to use hot water:
			for i in range(0, 1440):
				if occupancyPerson[p][i] > 0 and pResult[i] == 0:
					# filter out cooking and showering/bathing
					if (i < cookingTime or i > cookingTime + cookingDuration + 30):
						options.append(i)

			# Now calculate the tap usage based on the time being active
			tapmoments = random.sample(options, (int(len(options) / random.randint(120, 150))))
			for i in tapmoments:
				pResult[i] = 0.083 * powerPerLitre * random.randint(25,50)

			# Merge the result
			for i in range(0, len(pResult)):
				result[i] += pResult[i]

		return result

# Thermostat setpoints profile based on the occupancy and occupants preferences
# Note that this does not include a smart thermostat implementation that preheats
class Thermostat(HeatDevice):
	def __init__(self, consumption = 0):
		self.generate(consumption)
		self.Setpoints = [0.0]
		self.StartTimes = [0]

	def generate(self, consumption = 0):
		pass

	def simulate(self, timeintervals, day, persons, occupancy):
		# First select the highest setpoint
		heatingSetpoint = 0.0
		for p in persons:
			if p.thermostatSetpoint > heatingSetpoint:
				heatingSetpoint = p.thermostatSetpoint

		# Make a vector with all the temps
		setpoints = [0.0] * timeintervals
		for i in range(0, timeintervals):
			if occupancy[i] > 0:
				setpoints[i] = heatingSetpoint

		# Now select the edges
		for i in range(1, timeintervals):
			if setpoints[i] != setpoints[i-1]:
				#Edge
				#Random higher setpoint
				if setpoints[i] > 0.001 and random.randint(0,9) < 2:
					self.Setpoints.append(setpoints[i]+1.0)
					self.StartTimes.append(day*1440 + i)
				else:
					self.Setpoints.append(setpoints[i])
					self.StartTimes.append(day*1440 + i)

	def writeDevice(self, hnum):
		config.writer.writeDeviceThermostat(self, hnum)

# Heat generated by persons
class PersonGain(HeatDevice):
	def __init__(self, consumption = 0):
		pass

	def generate(self, consumption = 0):
		pass

	def simulate(self, timeintervals, persons, occupancyPerson):
		HeatProfile = [0] * timeintervals
		for p in range(0, len(persons)):
			for i in range(0, len(occupancyPerson[p])):
				HeatProfile[i] += occupancyPerson[p][i] * persons[p].heatGeneration

		return HeatProfile


class Ventilation(HeatDevice):
	def __init__(self, consumption = 0):
		self.MaxAirflow = 300 #M3/h
		self.IdleAirflow = 30 # M3/h
		self.PersonAirFlow = 30 # M3/h per person
		self.CookingAirFlow = 150 #M3/h when cooking (additional)
		self.VentilationProfile = []

	def generate(self, consumption = 0):
		pass

	def simulate(self, timeintervals, occupancy):
		self.VentilationProfile = [self.IdleAirflow] * timeintervals
		for i in range(0, len(occupancy)):
			self.VentilationProfile[i] += occupancy[i] * self.PersonAirFlow
			self.VentilationProfile[i] = min(self.VentilationProfile[i], self.MaxAirflow )

		# Initial profile, notice that ventilation will be incremented using other activities such as cooking and showers!
		return self.VentilationProfile
