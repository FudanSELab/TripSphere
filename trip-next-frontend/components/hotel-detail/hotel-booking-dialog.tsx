"use client";

import { useState, useTransition, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createOrder } from "@/actions/order";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Field, FieldError, FieldLabel } from "@/components/ui/field";
import { Input } from "@/components/ui/input";
import { Spinner } from "@/components/ui/spinner";

export interface HotelBookingDefaults {
  isAuthenticated: boolean;
  checkInDate: string;
  checkOutDate: string;
  contactName: string;
  contactEmail: string;
}

interface HotelBookingDialogProps {
  skuId: string;
  skuName: string;
  price: number;
  defaults: HotelBookingDefaults;
}

export function HotelBookingDialog({
  skuId,
  skuName,
  price,
  defaults,
}: HotelBookingDialogProps) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [requestId, setRequestId] = useState("");
  const [checkInDate, setCheckInDate] = useState(defaults.checkInDate);
  const [checkOutDate, setCheckOutDate] = useState(defaults.checkOutDate);
  const [quantity, setQuantity] = useState(1);
  const [contactName, setContactName] = useState(defaults.contactName);
  const [contactPhone, setContactPhone] = useState("");
  const [contactEmail, setContactEmail] = useState(defaults.contactEmail);
  const [error, setError] = useState<string>();
  const [isPending, startTransition] = useTransition();

  if (!defaults.isAuthenticated) {
    return (
      <Button asChild size="sm" className="px-6">
        <Link href="/signin">预订</Link>
      </Button>
    );
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(undefined);

    if (checkOutDate <= checkInDate) {
      setError("退房日期必须晚于入住日期");
      return;
    }

    startTransition(async () => {
      const currentRequestId = requestId || crypto.randomUUID();
      if (!requestId) setRequestId(currentRequestId);
      const result = await createOrder({
        requestId: currentRequestId,
        skuId,
        checkInDate,
        checkOutDate,
        quantity,
        contact: {
          name: contactName,
          phone: contactPhone,
          email: contactEmail,
        },
      });
      if (!result.success) {
        setError(result.error);
        return;
      }

      setOpen(false);
      router.push("/orders");
      router.refresh();
    });
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(nextOpen) => {
        if (!isPending) {
          setOpen(nextOpen);
          if (nextOpen) {
            setError(undefined);
            setRequestId(crypto.randomUUID());
          } else {
            setRequestId("");
          }
        }
      }}
    >
      <DialogTrigger asChild>
        <Button size="sm" className="px-6">
          预订
        </Button>
      </DialogTrigger>
      <DialogContent>
        <form onSubmit={handleSubmit} className="flex flex-col gap-5">
          <DialogHeader>
            <DialogTitle>预订 {skuName}</DialogTitle>
            <DialogDescription>
              当前展示参考价 ¥{Math.round(price)}
              ，订单以所选日期的实际库存价格结算。
            </DialogDescription>
          </DialogHeader>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field>
              <FieldLabel htmlFor={`check-in-${skuId}`}>入住日期</FieldLabel>
              <Input
                id={`check-in-${skuId}`}
                type="date"
                min={defaults.checkInDate}
                value={checkInDate}
                onChange={(event) => setCheckInDate(event.target.value)}
                disabled={isPending}
                required
              />
            </Field>
            <Field>
              <FieldLabel htmlFor={`check-out-${skuId}`}>退房日期</FieldLabel>
              <Input
                id={`check-out-${skuId}`}
                type="date"
                min={checkInDate}
                value={checkOutDate}
                onChange={(event) => setCheckOutDate(event.target.value)}
                disabled={isPending}
                required
              />
            </Field>
          </div>

          <Field>
            <FieldLabel htmlFor={`quantity-${skuId}`}>房间数量</FieldLabel>
            <Input
              id={`quantity-${skuId}`}
              type="number"
              min={1}
              max={10}
              value={quantity}
              onChange={(event) => setQuantity(event.target.valueAsNumber)}
              disabled={isPending}
              required
            />
          </Field>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field>
              <FieldLabel htmlFor={`contact-name-${skuId}`}>
                联系人姓名
              </FieldLabel>
              <Input
                id={`contact-name-${skuId}`}
                value={contactName}
                onChange={(event) => setContactName(event.target.value)}
                disabled={isPending}
                autoComplete="name"
                required
              />
            </Field>
            <Field>
              <FieldLabel htmlFor={`contact-phone-${skuId}`}>
                联系电话
              </FieldLabel>
              <Input
                id={`contact-phone-${skuId}`}
                type="tel"
                value={contactPhone}
                onChange={(event) => setContactPhone(event.target.value)}
                disabled={isPending}
                autoComplete="tel"
                required
              />
            </Field>
          </div>

          <Field>
            <FieldLabel htmlFor={`contact-email-${skuId}`}>联系邮箱</FieldLabel>
            <Input
              id={`contact-email-${skuId}`}
              type="email"
              value={contactEmail}
              onChange={(event) => setContactEmail(event.target.value)}
              disabled={isPending}
              autoComplete="email"
              required
            />
          </Field>

          {error && (
            <FieldError id={`booking-error-${skuId}`} aria-live="polite">
              {error}
            </FieldError>
          )}

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => setOpen(false)}
              disabled={isPending}
            >
              取消
            </Button>
            <Button type="submit" disabled={isPending}>
              {isPending && <Spinner />}
              {isPending ? "创建订单中…" : "确认下单"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
