import React from "react";
import { Button } from "semantic-ui-react";

export default function RowActions({
  onEdit,
  onView,
  onDelete,
  editDisabled = false,
  viewDisabled = false,
  viewHref,
}) {
  const handleView = () => {
    if (viewDisabled) return;
    if (viewHref) {
      window.location.href = viewHref;
    } else if (onView) {
      onView();
    }
  };

  return (
    <>
      <Button color="blue" disabled={editDisabled} onClick={onEdit}>
        Edit
      </Button>
      <Button
        color="blue"
        disabled={viewDisabled}
        as={viewHref ? "a" : undefined}
        onClick={handleView}
      >
        View
      </Button>
      <Button color="red" disabled={editDisabled} onClick={onDelete}>
        Delete
      </Button>
    </>
  );
}
