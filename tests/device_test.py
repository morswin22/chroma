import json
import unittest

from pychroma import Connection, Device, DeviceError, parse_rgb


class DeviceTest(unittest.TestCase):
  def setUp(self):
    with open('./tests/assets/example.json', 'r') as file:
      config = json.load(file)

    self.connection = Connection(config['chroma'])

  def tearDown(self):
    self.connection.stop()

  def test_valid_devices(self):
    for device_name in Device.TYPES['grid'] + Device.TYPES['array']:
      Device(self.connection.url, device_name)

  def test_invalid_devices(self):
    for device_name in Device.TYPES['grid'] + Device.TYPES['array']:
      with self.assertRaises(DeviceError) as error:
        Device(self.connection.url, device_name[::-1])

      self.assertEqual(str(error.exception), "Unknown device type")

  def test_device_size(self):
    for device_name in Device.TYPES['grid'] + Device.TYPES['array']:
      device = Device(self.connection.url, device_name)

      self.assertTrue(device.type in Device.TYPES)

      if device.type == 'array':
        self.assertTrue(isinstance(device.size, int))
      elif device.type == 'grid':
        self.assertTrue(isinstance(device.size, tuple))
  
  def test_in_bounds(self):
    for device_name in Device.TYPES['grid'] + Device.TYPES['array']:
      device = Device(self.connection.url, device_name)

      if device.type == 'array':
        with self.assertRaises(DeviceError) as error:
          device.set_grid((0,0), (0,0,0))
        
        self.assertEqual(str(error.exception), "Can not check is in grid on non-grid device")
        
        for pos in range(device.size):
          self.assertTrue(device.in_array(pos))

        for invalid_pos in [-1, device.size, device.size + 1]:
          self.assertFalse(device.in_array(invalid_pos))

          with self.assertRaises(DeviceError) as error:
            device.set_array(invalid_pos, (0,0,0))

          self.assertEqual(str(error.exception), "Position out of array bounds")

      elif device.type == 'grid':
        with self.assertRaises(DeviceError) as error:
          device.set_array(0, (0,0,0))
        
        self.assertEqual(str(error.exception), "Can not check is in array on non-array device")
        
        for x in range(device.size[0]):
          for y in range(device.size[1]):
            self.assertTrue(device.in_grid((x, y)))

        for invalid_pos in [(-1, 0), (0, -1), (device.size[0], 0), (0, device.size[1]), (device.size[0] + 1, 0), (0, device.size[1] + 1)]:
          self.assertFalse(device.in_grid(invalid_pos))

          with self.assertRaises(DeviceError) as error:
            device.set_grid(invalid_pos, (0,0,0))

          self.assertEqual(str(error.exception), "Position out of grid bounds")

  @unittest.expectedFailure
  def test_parse_color(self):
    for invalid_color in [(0,0,0,0), (0,), 1, '#33344', '#3334443', True, None, (-10,-10,-10), (257,264,326), '#hhhhhh']:
      with self.assertRaises(DeviceError) as error:
        parse_color(invalid_color)
      
      self.assertEqual(str(error.exception), "Can not parse inserted color")
    
    valid = [0, 127, 255]
    for r in valid:
      for g in valid:
        for b in valid:
          self.assertTrue(isinstance(parse_color((r,g,b)), int)) 

  def test_state(self):
    for device_name in Device.TYPES['grid'] + Device.TYPES['array']:
      device = Device(self.connection.url, device_name)

      device.set_none()
      self.assertEqual(device.state, 'NONE')

      device.set_static((0,0,0))
      self.assertEqual(device.state, 'STATIC')

      if device.type == 'array':
        device.set_array(0, (0,0,0))
      elif device.type == 'grid':
        device.set_grid((0,0), (0,0,0))
      
      self.assertEqual(device.state, 'CUSTOM')

  def test_fill_and_clear(self):
    for device_name in Device.TYPES['grid'] + Device.TYPES['array']:
      device = Device(self.connection.url, device_name)

      if device.type == 'array':
        for pos in range(device.size):
          device.set_array(pos, (127, 127, 127))
          self.assertEqual(device.array[pos], parse_rgb((127, 127, 127)))

        device.clear()

        for pos in range(device.size):
          self.assertEqual(device.array[pos], 0)

      elif device.type == 'grid':
        for x in range(device.size[0]):
          for y in range(device.size[1]):
            device.set_grid((x, y), (127, 127, 127))
            self.assertEqual(device.grid[y][x], parse_rgb((127, 127, 127)))

        device.clear()

        for x in range(device.size[0]):
          for y in range(device.size[1]):
            self.assertEqual(device.grid[y][x], 0)
