/// Error model shared across the application layers.
///
/// Domain/application code should throw and propagate [Failure] subtypes
/// instead of leaking framework or transport-specific exceptions.
sealed class Failure implements Exception {
  const Failure(this.message);

  final String message;

  @override
  String toString() => message;
}

class NetworkFailure extends Failure {
  const NetworkFailure(super.message);
}

class TimeoutFailure extends Failure {
  const TimeoutFailure(super.message);
}

class ServerFailure extends Failure {
  const ServerFailure(super.message);
}

class UnknownFailure extends Failure {
  const UnknownFailure(super.message);
}
