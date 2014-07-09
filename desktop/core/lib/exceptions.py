import sys
import traceback



class StructuredException(Exception):
  """
  Many exceptions in this application are a string and some data
  that applies to.  The middleware will take these exceptions
  and render them.
  """
  def __init__(self, code, message, data=None, error_code=500):
    Exception.__init__(self, message)
    self.code = code
    self.message = message
    self.data = data
    self.error_code = error_code

    # Traceback is only relevant if an exception was thrown, caught, and we reraise with this exception.
    (type, value, tb) = sys.exc_info()
    self.traceback = traceback.extract_tb(tb)

  def __str__(self):
    return "%s (code %s): %s" % (self.message, self.code, repr(self.data))

  @property
  def response_data(self):
    return dict(code=self.code,
                message=self.message,
                data=self.data,
                traceback=self.traceback)

class MessageException(StructuredException):
  """
  Explicitly specified msg/filename exception.

  This has been superceded by PopupException.
  """
  def __init__(self, msg, filename=None, error_code=500):
    StructuredException.__init__(self,
      code="GENERIC_MESSAGE",
      message=msg,
      data=dict(filename=filename),
      error_code=error_code)


